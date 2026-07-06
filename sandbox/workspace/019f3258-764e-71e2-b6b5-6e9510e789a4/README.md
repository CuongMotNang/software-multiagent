# Personal Task Manager

A simple, client-side task management application built with vanilla JavaScript, HTML, and CSS. All data is stored locally in the browser using localStorage.

## Features

- ✅ **Create tasks** with title (1-200 chars) and optional description (0-1000 chars)
- 📋 **View task list** sorted by status (pending first) and creation date
- 🔍 **Filter tasks** by All, Pending, or Completed
- ✏️ **Edit tasks** (only pending tasks can be edited)
- ✅ **Toggle completion status** with a single click
- 🗑️ **Delete tasks** with confirmation dialog
- 📱 **Responsive design** - works on mobile, tablet, and desktop
- ♿ **Accessible** - ARIA labels, keyboard navigation, focus management
- 🔄 **Persistent storage** using localStorage with memory fallback

## Project Structure

```
.
├── index.html          # Main HTML file
├── css/
│   └── styles.css      # All styles
├── js/
│   ├── app.js          # Main application logic
│   ├── storage.js      # StorageService (localStorage abstraction)
│   ├── task.js         # Task model and validation
│   └── ui.js           # UI rendering and DOM manipulation
└── README.md           # This file
```

## How to Run

### Option 1: Open directly in browser

Simply open `index.html` in any modern web browser (Chrome, Firefox, Safari, Edge).

```bash
# On macOS
open index.html

# On Linux
xdg-open index.html

# On Windows
start index.html
```

### Option 2: Use a local server (recommended)

Using a local server ensures proper module loading:

```bash
# Using Python 3
python -m http.server 8080

# Using Node.js (if you have npx)
npx serve .

# Using PHP
php -S localhost:8080
```

Then open `http://localhost:8080` in your browser.

## Browser Compatibility

- Chrome 80+
- Firefox 75+
- Safari 13.1+
- Edge 80+

## Data Storage

- Tasks are stored in the browser's `localStorage` under the key `ptm_tasks`
- If localStorage is unavailable (e.g., private mode), data falls back to memory storage
- Maximum task limit: 1000 tasks
- Data persists across browser sessions (unless in private mode)

## Keyboard Shortcuts

- `Escape` - Close modals
- `Tab` - Navigate between interactive elements
- `Enter` / `Space` - Activate buttons and checkboxes

## Design Document

This application is based on the Design Document for Personal Task Manager v1.0, which includes:

- Process Model with user flows
- Data Model (Task entity)
- UI Screen specifications
- Edge case handling
- Accessibility requirements (ARIA, contrast, responsive)
