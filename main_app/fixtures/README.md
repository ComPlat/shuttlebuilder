# Fixtures for `sdc_teach`

## `teacher.json` — crawl user

A superuser for the `jest` crawl database (`test_db.sqlite3`), so `sdc_teach` can also
crawl the logged-in UI. The accompanying `ElnUser` profile is created automatically
by the `post_save` signal in `main_app/models.py`.

- Username: `teacher`
- Password: `teach-me-2026`

The password in the JSON is the Django hash of the plaintext above. This account only
exists in the throwaway crawl database — do not load it into the production/default DB.

Run `sdc_teach` with this user:

```sh
poetry run python manage.py sdc_teach --fixture teacher --user teacher --password teach-me-2026
```

Add `--no-ask` when no documentation questions should be asked in the terminal.
