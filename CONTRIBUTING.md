# Contributing to AI TOOL NEWS

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Adding new AI tools to the monitoring list

## Adding New Tools
The easiest way to contribute is to expand our monitoring capabilities.

1. Fork the repo and create your branch from `main`.
2. Open `targets.json`.
3. Add a new entry following this format:
   ```json
   {
       "name": "New Tool Name",
       "accounts": ["@OfficialAccount"]
   }
   ```
4. If it's a new category, you can create a new category block.
5. Submit a Pull Request!

## Development Process
1. Ensure your API key is in `.env` (passed to `.gitignore`).
2. Run `collect_ai_news.py` to verify the new target works.
3. Run `build_site.py` to ensure the site builds without errors.

## License
By contributing, you agree that your contributions will be licensed under its MIT License.
