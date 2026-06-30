content = open(r"C:\Users\HP\crypto-arbitrage-tracker\scanner.py", encoding="utf-8").read()

old = '''    parser.add_argument('--once',        action='store_true',
                        help='Run once and exit (no loop)')
    args = parser.parse_args()'''

new = '''    parser.add_argument('--once',        action='store_true',
                        help='Run once and exit (no loop)')
    parser.add_argument('--symbols',     type=str, default=None,
                        help='Comma-separated list of symbols to scan (overrides default)')
    args = parser.parse_args()

    global SCAN_SYMBOLS
    if args.symbols:
        SCAN_SYMBOLS = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]'''

content = content.replace(old, new)

open(r"C:\Users\HP\crypto-arbitrage-tracker\scanner.py", "w", encoding="utf-8").write(content)
print("Scanner patched")