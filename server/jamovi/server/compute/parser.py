
import ast
import base64
import re


class Parser:

    _SPECIAL_CHARS = ' ~!@#$%^&*()+=-[]{};,<>?/\\'

    @staticmethod
    def parse(str):

        escaped = Parser.escape(str.strip())  # escape column names
        tree = ast.parse(escaped)

        if len(tree.body) == 0:
            return None

        tree = tree.body[0].value

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                node.id = Parser.unescape_chunk(node.id)

        return tree

    @staticmethod
    def escape_chunk(chunk):

        if len(chunk) == 0:
            return chunk
        elif chunk == '^':
            return '**'
        elif chunk == 'and':
            return 'and'
        elif chunk == 'or':
            return 'or'
        elif chunk == 'not':
            return 'not'
        elif chunk == '=':
            return '=='
        elif chunk == '==':
            return '=='
        elif chunk == '>=':
            return '>='
        elif chunk == '<=':
            return '<='
        elif chunk == '!=':
            return '!='
        elif len(chunk) == 1 and chunk in Parser._SPECIAL_CHARS:
            return chunk
        elif chunk.startswith('"') and chunk.endswith('"'):
            return chunk
        elif re.match(r'^[0-9]*\.?[0-9]+$', chunk):
            return chunk
        else:
            return '_' + base64.b16encode(chunk.encode('utf-8')).decode('utf-8')

    @staticmethod
    def unescape_chunk(chunk):
        if not chunk.startswith('_'):
            raise ValueError()
        chunk = chunk[1:]
        return base64.b16decode(chunk.encode('utf-8')).decode('utf-8')

    @staticmethod
    def escape(str):

        # encodes column names into base16

        s = 0
        e = 0
        n = len(str)
        q = ''

        chunks = list()

        while True:

            while s < n:
                sc = str[s]
                if sc in '"\'`':
                    q = sc
                    break
                if sc not in Parser._SPECIAL_CHARS:
                    break
                else:
                    if sc == '=' or sc == '!' or sc == '>' or sc == '<':
                        if s + 1 < n and (str[s + 1] == '='):
                            s += 1
                            sc += '='
                    chunks.append(sc)
                    s += 1

            e = s + 1

            while e < n:
                ec = str[e]
                if ec == q:
                    if q == '`':
                        term = ''.join(str[s + 1:e])
                    else:
                        term = '"' + ''.join(str[s + 1:e]) + '"'
                    chunks.append(term)
                    q = ''
                    break
                elif q is '' and ec in Parser._SPECIAL_CHARS:
                    term = ''.join(str[s:e])
                    chunks.append(term)
                    if ec == '=' or ec == '!' or ec == '>' or ec == '<':
                        if e + 1 < n and (str[e + 1] == '='):
                            e += 1
                            ec += '='
                    chunks.append(ec)
                    break
                else:
                    e += 1
            else:
                term = ''.join(str[s:e])
                chunks.append(term)

            if e >= n:
                break

            s = e + 1

        i = 0
        while i < len(chunks) - 1:
            # $source is special, so here we put $ + source back together
            chunk = chunks[i]
            if chunk == '$' and chunks[i + 1] == 'source':
                chunks[i] = '$source'
                chunks.pop(i + 1)
            else:
                i += 1

        chunks = map(Parser.escape_chunk, chunks)

        return ''.join(chunks)
