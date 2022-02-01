from neighborly import loaders


def main():
    loaders.load_names("first_name", names=["John", "Calvin", "Sarah", "Caleb"])

    loaders.load_names("last_name", names=["Pizza", "Apple", "Blueberry", "Avocado"])

    initialize_name_generator()

    print(get_name("#first_name# #last_name#"))


if __name__ == "__main__":
    main()
