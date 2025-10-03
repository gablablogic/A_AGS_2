def calculate_average(numbers: list[float]) -> float:
    """
    Calculate the average of a list of numbers.

    Parameters:
    numbers (list[float]): A list of numbers to calculate the average.

    Returns:
    float: The average of the numbers in the list.
    """
    import subprocess
    import sys

    # Programmatically install dependencies if not already installed
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'numpy'])
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        return None

    import numpy as np

    if not numbers:
        return 0.0
    return np.mean(numbers)


def main():
    # Exemple de données de test
    data = [10, 20, 30, 40]
    result = calculate_average(data)
    print(f"Liste : {data}")
    print(f"Moyenne : {result}")


if __name__ == "__main__":
    main()