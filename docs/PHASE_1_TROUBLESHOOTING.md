# Phase 1 Troubleshooting

## UI opens but registration/search does not work
Use the updated package and reinstall dependencies:

```powershell
pip install -r requirements.txt
python run.py
```

The application now includes the `email-validator` dependency and seeds demo travel inventory on first startup.

Demo search destinations: Goa, Delhi, Jaipur, Manali.
Demo flight departure cities: Mumbai and Delhi.
