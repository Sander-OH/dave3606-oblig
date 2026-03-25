import struct
import sys


def read_uint32(f):
    """Read an unsigned 32-bit integer"""
    data = f.read(4)
    if len(data) < 4:
        raise EOFError("Unexpected end of file while reading uint32")
    return struct.unpack("I", data)[0]


def read_string(f):
    """Read a length-prefixed UTF-8 string"""
    length = read_uint32(f)
    data = f.read(length)
    if len(data) < length:
        raise EOFError("Unexpected end of file while reading string")
    return data.decode("utf-8")


def read_lego_set(filename):
    with open(filename, "rb") as f:
        set_id = read_string(f)
        name = read_string(f)
        year = read_uint32(f)
        category = read_string(f)
        image = read_string(f)

        print("=== LEGO SET ===")
        print(f"ID: {set_id}")
        print(f"Name: {name}")
        print(f"Year: {year}")
        print(f"Category: {category}")
        print(f"Image URL: {image}")
        print()

        inventory_count = read_uint32(f)
        print(f"Inventory items: {inventory_count}")
        print()

        for i in range(inventory_count):
            brick_type_id = read_string(f)
            color_id = read_uint32(f)
            brick_name = read_string(f)
            brick_image = read_string(f)
            count = read_uint32(f)

            print(f"Item #{i + 1}")
            print(f"  Brick Type ID: {brick_type_id}")
            print(f"  Color ID: {color_id}")
            print(f"  Name: {brick_name}")
            print(f"  Image URL: {brick_image}")
            print(f"  Count: {count}")
            print()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python read_lego_bin.py <binary_file>")
        sys.exit(1)

    filename = sys.argv[1]
    read_lego_set(filename)