# Aqua Launch — Setup Guide

This template creates the animated blue-green profile shown in this folder: a self-typing ASCII portrait, dense morphing wordmark, live contribution field, moving spacecraft, profile signal, and language stack.

## Fastest setup

1. Create a public repository named exactly like your GitHub username.
2. Copy **the contents** of `Aqua-Launch` into it.
3. Replace `assets/profile-source.png` with your portrait source.
4. Edit `config.json` and the contact links in `README.md`.
5. Install Pillow and run `python scripts/generate.py --demo`.
6. Push the repository and run the included GitHub Action once.

## Requirements

- A GitHub account
- Python 3.10 or newer for local generation
- Pillow, installed through the included requirements file
- Git, GitHub Desktop, or GitHub’s web uploader

No paid API or external stats-card service is required.

## 1. Create your profile repository

Create a **public** repository with exactly the same name as your GitHub username. GitHub renders its root `README.md` on your profile.

## 2. Copy the template

Copy everything **inside** `Aqua-Launch` into your repository root:

```text
your-username/
├── .github/workflows/update-profile.yml
├── assets/
│   ├── profile-source.png
│   ├── identity.svg
│   ├── contributions.svg
│   └── signal.svg
├── scripts/
│   ├── generate.py
│   └── requirements.txt
├── config.json
├── README.md
└── SETUP.md
```

Important: `.github` may be hidden by your file manager. Copy it or automatic updates will not work.

## 3. Add your portrait source

Replace `assets/profile-source.png` with your own image. For the clearest ASCII portrait, use:

- A high-resolution portrait
- Strong contrast between the person and background
- A removed, white, or very light background
- A roughly square or portrait crop

Keep the filename, or change the `photo` path in `config.json`. The original photo is never displayed in the README; the generator converts it into SVG text characters.

## 4. Personalize `config.json`

Replace every example value:

- `username`: your exact GitHub username
- `name`: your full name
- `wordmark`: the large animated ASCII text
- `role`, `location`, and `status`: your profile information
- `website`: your complete website URL
- `photo`: the path to your source portrait
- `skills`: up to six short skill names

For the cleanest wordmark, use no more than eight uppercase letters, numbers, or spaces. The built-in alphabet supports `A–Z`, `0–9`, and spaces.

Example:

```json
{
  "username": "your-username",
  "name": "Your Name",
  "wordmark": "YOURNAME",
  "photo": "assets/profile-source.png"
}
```

## 5. Update the contact buttons

At the bottom of `README.md`, replace the portfolio, GitHub, and email URLs. Remove any button you do not need.

## 6. Install and generate

Run these commands from the repository root:

```bash
python -m pip install -r scripts/requirements.txt
python scripts/generate.py --demo
```

The demo command verifies the portrait and layout without needing GitHub data. Then generate with live public data:

```bash
python scripts/generate.py
```

With `GITHUB_TOKEN`, the generator uses GitHub GraphQL for contributions. Without a token, it falls back to GitHub’s public contribution page. If local requests are rate-limited, use the GitHub Action instead.

## 7. Preview the result

- Open `README.md` in VS Code and press `Ctrl+Shift+V`.
- Push the repository for the exact GitHub rendering and animation behavior.

Do not rename the three generated SVG files unless you also change their paths in `README.md`.

## 8. Enable automatic updates

Push the repository and open **Actions → Update Aqua Launch → Run workflow**. The workflow installs Pillow and regenerates all assets every day.

If the workflow cannot push:

1. Open **Settings → Actions → General**.
2. Find **Workflow permissions**.
3. Select **Read and write permissions**.
4. Save and run the workflow again.

## Customize the palette

Edit these constants near the top of `scripts/generate.py`:

```python
TEAL = "#43ead3"
MINT = "#83ffe8"
BLUE = "#4387ff"
PURPLE = "#9b6cff"
```

Rerun the generator after changing colors, content, or the source portrait.

## AI-assisted setup prompt

Attach or place your portrait image in the repository, then copy this prompt into a coding assistant:

```text
Set up the Aqua Launch GitHub profile template in this repository for me.

My details:
- GitHub username: [USERNAME]
- Full name: [NAME]
- ASCII wordmark, maximum 8 characters: [WORDMARK]
- Role: [ROLE]
- Location: [LOCATION]
- Short status: [STATUS]
- Website: [WEBSITE URL]
- Skills, maximum 6: [SKILLS]
- Contact email: [EMAIL]
- Portrait image path: [PATH TO MY IMAGE]

Please inspect the existing repository first. Copy or prepare my portrait as assets/profile-source.png without replacing the original source unless necessary. Update config.json and the contact links in README.md, preserve the Aqua Launch colors and animations, install the requirements, generate a demo first, then use live GitHub data if internet access is available. Verify that the portrait is truly ASCII, the wordmark fits, all SVG files are valid, all local Markdown links work, and the workflow is correctly placed. Do not modify unrelated files, and do not commit or push unless I explicitly ask.
```

## Animation behavior

- The portrait types row by row like a terminal image renderer.
- The dense wordmark types in once and morphs between two character sets.
- Contribution cells reveal in a diagonal wave.
- The spacecraft moves only horizontally.
- Two projectiles shoot upward at staggered intervals.
- Reduced-motion preferences disable continuous CSS animations.

## Common problems

- **The portrait is noisy:** use a lighter or removed background and stronger contrast.
- **The wordmark is clipped:** shorten `wordmark` to eight characters or fewer.
- **Live contributions fail locally:** run the GitHub Action, which receives an automatic token.
- **Animations do not move in a screenshot:** open the actual `README.md`; screenshots capture only one animation frame.
