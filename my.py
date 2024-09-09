import os

def count_images(directory, image_extensions):
    count = 0

    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                count += 1

    return count

# Replace 'combined' with the path to your desired directory
directory = 'combined'
image_extensions = ['.jpg', '.png', '.gif']  # Add more extensions if needed
image_count = count_images(directory, image_extensions)
print(f"Number of images in subfolders of '{directory}': {image_count}")