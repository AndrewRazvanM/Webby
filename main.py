import sys
from crawl import crawl_page

def main():
    command_line_arg = sys.argv
    nr_arg = len(command_line_arg)

    if nr_arg < 2:
        print("no website provided")
        sys.exit(1)
    if nr_arg >= 3:
        print("too many arguments provided")
        sys.exit(1)

    url = command_line_arg[1]

    print(f"starting crawl of: {command_line_arg[1]}")
    page_data = crawl_page(url)
    print(page_data)

if __name__ == "__main__":
    main()
