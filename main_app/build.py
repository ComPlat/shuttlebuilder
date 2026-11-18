"""Build helpers for ShuttleInstance.build() (M1).

The orchestrator owns the public interface below (`BuildError`); the build
pipeline worker fills in the rest of this module.
"""


class BuildError(Exception):
    """A Shuttle build failed.

    - `public_message`: neutral, translated text that may be shown to any user.
    - `detail`: short, **redacted** technical detail (e.g. the first compiler
      lines, or the name of the file that failed). May be shown to staff only.
      Never contains passwords, tokens or rendered sources.
    - `reference`: short id that is also written to the server log, so a user
      can quote it to an administrator.
    """

    def __init__(self, public_message, detail="", reference=""):
        super().__init__(public_message)
        self.public_message = str(public_message)
        self.detail = detail
        self.reference = reference
