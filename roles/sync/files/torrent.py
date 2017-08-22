import os
import requests
import bencode

__author__ = 'aluetjen'


class Torrent:
    download_server = 'https://seeder.basechord.com'
    local_download_path = '.'

    def __init__(self):
        self.metadata = None
        self.files = None
        self.name = None
        self.creation_date = None
        self.priority = 100
        self.local_root_path = None
        self.pieces = None
        self.piece_length = None
        self.download_server = Torrent.download_server
        self.local_download_path = Torrent.local_download_path

    def load(self, torrent_file):
        with open(torrent_file, 'rb') as torrent_file:
            torrent_content = torrent_file.read()
            self.metadata = bencode.bdecode(torrent_content)

        self.files = self.metadata['info']['files']
        self.name = self.metadata['info']['name'].decode('ascii')
        self.creation_date = self.metadata['creation date']
        if 'priority' in self.metadata:
            self.priority = self.metadata['priority']
        self.pieces = self.metadata['info']['pieces']
        self.piece_length = self.metadata['info']['piece length']
        self.local_root_path = os.path.join(self.local_download_path, self.name)

    def get_local_files(self):
        return [(self._concatenate_local_path(file['path']), int(file['length']))
                for file in self.files]

    def get_total_length(self):
        total_length = 0
        for file in self.files:
            total_length += int(file['length'])
        return total_length

    def get_number_of_pieces(self):
        pieces_length = len(self.pieces)
        return int(pieces_length / 20)

    def get_piece_request(self, index):
        """
        :rtype: PieceRequest
        """
        piece_length = self.piece_length
        effective_piece_length = 0
        target_offset = index * piece_length
        offset = 0

        files = []

        for file in self.files:
            file_length = file['length']
            file_offset_start = offset
            file_offset_end = offset + file_length
            if file_offset_start - piece_length < target_offset < file_offset_end:
                path_parts = file['path']

                piece_offset = 0
                file_piece_data_offset = target_offset - file_offset_start
                file_piece_data_length = piece_length

                if file_piece_data_offset < 0:
                    piece_offset = abs(file_piece_data_offset)
                    file_piece_data_length += file_piece_data_offset
                    file_piece_data_offset = 0

                if file_piece_data_offset + file_piece_data_length > file_length:
                    file_piece_data_length = file_length - file_piece_data_offset

                piece_file = PieceFile(
                    piece_offset=piece_offset,
                    piece_length=file_piece_data_length,
                    remote_url=self._concatenate_remote_url(path_parts),
                    local_file=self._concatenate_local_path(path_parts),
                    local_offset=file_piece_data_offset,
                    remote_offset=file_piece_data_offset,
                    total_length=file_length
                )

                effective_piece_length += piece_file.piece_length
                files.append(piece_file)

            offset += file_length

            if offset > target_offset + piece_length:
                break

        checksum = self.pieces[index * 20:(index + 1) * 20]

        request = PieceRequest(
            length=effective_piece_length,
            checksum=checksum,
            files=files
        )

        return request

    def _concatenate_remote_url(self, path_parts):
        relative_url = ''
        decoded_parts = [x.decode('utf-8') for x in path_parts]
        for part in decoded_parts:
            relative_url += '/' + part

        absolute_url = requests.utils.quote(self.name + relative_url)

        return self.download_server + '/' + absolute_url

    def _concatenate_local_path(self, decoded_parts):
        decoded_parts = [x.decode('utf-8') for x in decoded_parts]
        root = os.path.join(self.local_download_path, self.name)
        return os.path.join(root, *decoded_parts)


class PieceRequest:
    def __init__(self, length, checksum, files):
        self.length = length
        self.checksum = checksum
        self.files = files


class PieceFile:
    def __init__(self, piece_offset, piece_length, remote_url, remote_offset,
                 local_file, local_offset, total_length):
        self.piece_offset = piece_offset
        self.piece_length = piece_length
        self.remote_url = remote_url
        self.remote_offset = remote_offset
        self.local_path = local_file
        self.local_offset = local_offset
        self.total_length = total_length
