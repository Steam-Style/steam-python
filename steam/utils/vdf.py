from typing import Any


class VDFParser:
    """
    A very basic VDF parser.
    """

    @classmethod
    def parse(cls, data: str) -> dict[str, Any]:
        """
        Parses a VDF string into a dictionary.

        Args:
            data: The VDF string to parse.

        Returns:
            The parsed VDF data as a dictionary.
        """
        result: dict[str, Any] = {}
        lines = data.splitlines()
        stack = [result]
        current_dict = result

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if line == '{':
                new_dict = {}
                last_key = list(current_dict.keys())[-1]
                current_dict[last_key] = new_dict
                stack.append(current_dict)
                current_dict = new_dict
            elif line == '}':
                current_dict = stack.pop()
            else:
                parts = line.split(None, 1)
                key = parts[0].strip('"')

                if len(parts) == 2:
                    value = parts[1].strip('"')
                    current_dict[key] = value
                else:
                    current_dict[key] = None

        return result
