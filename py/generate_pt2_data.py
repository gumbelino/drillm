import subprocess
import pandas as pd
import os

# --- Step 1: Run the R script to generate the progress report ---
print("Running R script to generate progress.csv...")
try:
    # Use subprocess.run to execute the R script.
    # The `capture_output=True` and `text=True` arguments help in capturing any output or errors.
    result = subprocess.run(
        ["Rscript", "pt2/check_progress.R"], capture_output=True, text=True, check=True
    )
    print("R script finished successfully.")
    if result.stdout:
        print("R script output:")
        print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f"Error running R script: {e}")
    print(f"Stdout: {e.stdout}")
    print(f"Stderr: {e.stderr}")
    # Exit if the R script fails.
    exit(1)

# Define the path to the CSV file
csv_file_path = "pt2/data/progress.csv"

# --- Step 2: Read the generated CSV file ---
if not os.path.exists(csv_file_path):
    print(f"Error: The file {csv_file_path} was not created by the R script.")
    exit(1)

print(f"Reading data from {csv_file_path}...")
try:
    # Read the CSV file into a pandas DataFrame.
    df = pd.read_csv(csv_file_path)
    print("CSV file read successfully.")
except FileNotFoundError:
    print(f"Error: {csv_file_path} not found.")
    exit(1)
except Exception as e:
    print(f"An error occurred while reading the CSV: {e}")
    exit(1)

# --- Step 3: Iterate through rows with N = 0 and call the data generation script ---
print("Checking for rows with N = 0 to generate new data...")
# Filter the DataFrame for rows where the 'N' column is 0.
rows_to_generate = df[df["N"] < 5]

if rows_to_generate.empty:
    print("No rows with N = 0 found. All data is complete.")
else:
    # Get the unique combinations of 'model' and 'prompt_uid' from the filtered rows.
    unique_combinations = rows_to_generate[
        ["model", "survey", "prompt_uid"]
    ].drop_duplicates()

    # Filter the unique combinations to only include models that contain "claude" (case-insensitive).
    unique_combinations = unique_combinations[
        unique_combinations["model"].str.contains("flash", case=False, na=False)
    ]

    print(
        f"Found {len(unique_combinations)} unique combinations with N = 0. Starting data generation..."
    )
    print(unique_combinations)
    for index, row in unique_combinations.iterrows():
        model = row["model"]
        survey = row["survey"]
        prompt_uid = row["prompt_uid"]

        # Construct the command to call the other Python script.
        # The number '5' is hardcoded as per your request.
        command = [
            "python",
            "./py/generate_llm_data.py",
            model,
            "1",
            "--survey",
            survey,
            "--prompt",
            prompt_uid,
        ]

        print(f"Executing command: {' '.join(command)}")
        try:
            # Execute the command using subprocess.run.
            # `check=True` will raise an error if the command fails.
            subprocess.run(command, check=True)
            print(
                f"Successfully generated data for model: {model}, prompt_uid: {prompt_uid}"
            )
        except subprocess.CalledProcessError as e:
            print(f"Error generating data for model: {model}, prompt_uid: {prompt_uid}")
            print(f"Subprocess failed with exit code {e.returncode}")
            # Continue to the next iteration even if one fails.

print("Script finished.")
