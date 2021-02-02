# ah-project

This was my Advanced Higher computing project (2019-2020). It never ended up getting marked, so I'm putting it here instead. It's a centralised version control system that uses the blockchain to ensure the change history of a file is not tampered with. Both the client and server applications are in this repository, as well as the report I wrote.

## Please don't copy this

A lot of stuff this application does is probably not a good idea for a real world app. Namely,

1. Homebrew crypto libraries are slow and hard to test for all insecurities
2. Code is sometimes duplicated across the client and server
3. The web framework and (to an extent) UI framework were built from the ground up, which is potentially a security risk and probably bad for performance.
4. There's a tonne of comments that probably don't need to be there, but the SQA seem to think they do.

These were mostly done for the sake of satisfying the SQA's requirements, with the exception of (2).

This repo might be useful for:

1. Current AH students looking for an example of report structure, etc.
2. A simple python implementation of crypto functions (`server/hash.py`, `server/aes/`, `server/rsa/`)
3. Making fun of my code and writing style.

If you're in any of these groups, then I hope you find this repo helpful. Here's some things which I hope will be good examples:

1. DIY DB Connection Pooling (`server/pool.py`)
2. DIY Request parsing (`server/context.py`)
3. DIY Crypto, including AES, RSA, and sha-256
4. A vague explanation of some of the concepts behind these algorithms in `writing/Compiled.md`

Again, this was never assessed, so don't take any of this as a perfect example

## Running

Both client and server are written on Python 3.8.

### Server

Install everything in `server/requirements.txt` and configure `server/config.py` to point to a MariaDB instance.

If running on a new database, run everything in `server/docs/schema.sql`. Then run `__init__.py` in the `server` folder.

### Client

Install everything in `client/requirements.txt`. You'll also need the `tkinter` module, which is standard in most Python installs.
Run `__init__.py` in the `client` folder.

## License

Code is under the MIT License.