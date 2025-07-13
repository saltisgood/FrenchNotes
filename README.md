# French Notes

## Structure

- Source files are in `src/`
- Grammar files are written in markdown, vocab files are CSVs
- You can generate the equivalent files in Anki format or Markdown with the included scripts (requires python >= 3.11)

## Scripts

To generate the compiled files:

1. First time only: install the requirements
  - `pip install -r requirements.txt`
2. Run the generator:
  - `python -m scripts.generate`
3. Files will be generated into `anki/` and `md/` for Anki and Markdown respectively
4. Can also run the generator with `--clear` to remove all destination files before generating

## Anki

- From the main area in the app, click on `Import File`
- Select the file you want to import
- Select the correct note type. For vocab files should be `French to English Noun`, for grammar should be `French Grammar`.
- Check the fields look correctly mapped and click `Import`

