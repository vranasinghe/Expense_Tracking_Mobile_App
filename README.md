# ExpenseTracker

A cross-platform personal finance app for tracking expenses and income, setting category budgets, and understanding spending through charts. Built with **React Native**, **Expo SDK 54** and **TypeScript**, with **Firebase Authentication** and **Cloud Firestore** for accounts and sync.

![Expo](https://img.shields.io/badge/Expo-SDK%2054-000020?logo=expo)
![React Native](https://img.shields.io/badge/React%20Native-0.81-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-Auth%20%7C%20Firestore-FFCA28?logo=firebase&logoColor=black)

---

## Features

| Area | What it does |
| --- | --- |
| **Onboarding** | Three-slide introduction with skip, followed by account creation or sign-in. |
| **Accounts** | Email and password sign-up and sign-in through Firebase Authentication. Runs in a local demo mode when Firebase is not configured. |
| **Starting balance** | Set a baseline balance on a custom numeric keypad. It can be changed later from the profile. |
| **Dashboard** | Current balance, total spent this month, income versus expenses, and recent transactions. |
| **Quick entry** | Bottom sheet with a keypad and category chips for logging an expense or an income in a few taps. |
| **Notifications** | In-app notification center with budget alerts, weekly summaries and reminders. Mark one or all as read. |
| **Analytics** | Month navigation, week/month/year views, a daily spending chart, income versus expense totals, and a category breakdown. |
| **Budgets** | Monthly limits per category with progress bars, an overall budget, and over-limit warnings. Press and hold a budget to delete it. |
| **History** | Search all transactions and filter by expense or income. Press and hold a transaction to delete it. |
| **Settings** | Display currency (`$`, `€`, `£`, `¥`), starting balance, preference toggles, help center, and log out. |
| **Sync** | Per-user real-time sync of profile, transactions, budgets and notifications through Firestore, protected by security rules. |

> **Demo mode:** without Firebase credentials the app keeps all data on the device and seeds sample transactions and budgets, so it can be explored straight away.

---

## Tech stack

- **App:** Expo SDK 54, React Native 0.81, React 19, TypeScript
- **Navigation:** Expo Router 6 (file-based routes, typed routes)
- **State:** Zustand with `persist` middleware over AsyncStorage
- **Backend:** Firebase Authentication, Cloud Firestore, Firebase Hosting (web build)
- **UI:** React Native Gifted Charts, Expo Linear Gradient, Ionicons, Poppins
- **Platforms:** iOS, Android and web (via React Native Web)

---

## Project structure

```text
.
├── backend/                    # Firebase project configuration
│   ├── firebase.json           # Firestore + Hosting config (serves mobile/dist)
│   ├── firestore.rules         # Per-user access rules
│   └── firestore.indexes.json
├── mobile/                     # Expo app
│   ├── app/
│   │   ├── (onboarding)/       # Splash slides, auth, starting balance
│   │   ├── (tabs)/             # Home, Analytics, Budgets, Profile
│   │   ├── _layout.tsx         # Root stack, fonts, web dialog host
│   │   └── index.tsx           # Entry redirect logic
│   ├── components/
│   │   ├── screens/            # Add sheet, notifications, transaction history
│   │   └── ui/                 # Keypad, cards, rows, chips, buttons
│   ├── constants/              # Colors, theme tokens, categories
│   ├── store/                  # Zustand store and shared types
│   └── utils/                  # Firebase client, currency and date helpers
├── demo-video/scripts/         # Optional tooling to record a narrated demo video
├── scripts/setup-and-run.bat   # Windows helper: install and start Expo
└── .github/workflows/ci.yml    # Type-check and web build on every push/PR
```

---

## Getting started

### Prerequisites

- [Node.js](https://nodejs.org/) 20 or newer
- [Expo Go](https://expo.dev/go) on a phone, or an Android emulator / iOS simulator

### Install and run

```bash
git clone https://github.com/vranasinghe/Expense_Tracking_Mobile_App.git
cd Expense_Tracking_Mobile_App/mobile
npm install
npm start
```

Then scan the QR code with Expo Go, or press `a` (Android), `i` (iOS) or `w` (web) in the terminal. On Windows you can also run `scripts\setup-and-run.bat`.

### Connect Firebase (optional)

1. Create a Firebase project and enable **Email/Password** sign-in and **Cloud Firestore**.
2. Register a web app in the Firebase console and copy its config.
3. Create `mobile/.env` from the template and fill in the values:

   ```bash
   cp mobile/.env.example mobile/.env
   ```

   | Variable | Description |
   | --- | --- |
   | `EXPO_PUBLIC_FIREBASE_API_KEY` | Web API key |
   | `EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN` | `<project-id>.firebaseapp.com` |
   | `EXPO_PUBLIC_FIREBASE_PROJECT_ID` | Project ID |
   | `EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET` | Storage bucket |
   | `EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Sender ID |
   | `EXPO_PUBLIC_FIREBASE_APP_ID` | App ID |

4. Restart the dev server. `.env` is git-ignored; never commit real credentials.

---

## Scripts

Run from `mobile/`:

| Command | Description |
| --- | --- |
| `npm start` | Start the Expo dev server |
| `npm run android` / `npm run ios` | Start and open on an emulator or simulator |
| `npm run web` | Start the web version |
| `npm run typecheck` | Type-check the project with `tsc` |
| `npm run build:web` | Export a static web build to `mobile/dist` |

---

## Deploying

The web build is served by Firebase Hosting and Firestore rules live in `backend/`.

```bash
cd mobile && npm run build:web
cd ../backend
npx firebase-tools login
npx firebase-tools use --add          # select your Firebase project
npx firebase-tools deploy --only hosting,firestore
```

---

## Data and security

- Each user's data is stored under `users/{uid}` in Firestore. The security rules only allow a signed-in user to read and write their own documents.
- Session persistence uses Firebase Auth with AsyncStorage; app state is persisted locally with Zustand.
- In demo mode nothing leaves the device.

---

## Roadmap

These appear in the UI or dependencies but are not wired up yet:

- [ ] Apply the dark mode preference across the app
- [ ] Enforce the biometric lock with `expo-local-authentication`
- [ ] Scheduled push reminders with `expo-notifications`
- [ ] Receipt photos on transactions with `expo-image-picker`
- [ ] CSV export and sharing
- [ ] Edit profile
- [ ] Google and Apple sign-in
- [ ] Unit and component tests

---

## Contributing

1. Create a branch from `main` (`feat/...`, `fix/...`, `docs/...`).
2. Keep changes focused and run `npm run typecheck` in `mobile/` before pushing.
3. Open a pull request describing what changed and how you tested it.
