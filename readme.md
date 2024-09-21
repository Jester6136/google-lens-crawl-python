# Image Metadata Extractor Using Google Lens

This Python script allows you to extract metadata for images by using Google Lens. The script takes a JSON file containing image URLs and processes the images in parallel to extract information like position, title, source, and link. The metadata is saved in a CSV file.

## Features
- Uses Selenium WebDriver to interact with Google Lens.
- Supports parallel processing using `ThreadPoolExecutor` to speed up image processing.
- Logs all important events and errors.
- Robust exception handling and retry mechanisms.
- Configurable file paths via command-line arguments.

## Prerequisites

- Python 3.x
- Google Chrome and ChromeDriver installed

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/google-lens-crawl-python.git
```
2. Navigate to the project directory:
```bash
cd google-lens-crawl-python
```

3. Install the required Python packages:
```bash
pip install -r requirements.txt
```

## Usage
Run the script with the JSON file containing image URLs and the desired output CSV file path:

```bash
python main.py /path/to/input.json /path/to/output.csv
```
- input.json: The JSON file that contains image IDs and URLs.
- output.csv: The CSV file where metadata will be saved.

## Example JSON File
```json
{
    "014693": "https://ichef.bbci.co.uk/news/1024/branded_vietnamese/CCC0/production/_127761425_phanvanthu.jpg",
    "014694": "https://thanhnien.mediacdn.vn/Uploaded/bienca/2022_02_12/anh-1-me-khoc-50.jpg",
    "014695": "https://btnmt.1cdn.vn/2020/07/27/anh-1-.jpg"
}
```

### Logs
The script logs events and errors, including retries on failures, making it easier to debug if something goes wrong.