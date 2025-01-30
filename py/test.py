import os


def greet_and_create_file():
    # Print "Hello"
    print("Hello")

    # Define the file path
    file_path = os.path.join(os.path.dirname(__file__), "../data/hello.txt")

    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Write "Hello there" to the file
    with open(file_path, "w") as file:
        file.write("Hello there")


# Call the function
greet_and_create_file()
