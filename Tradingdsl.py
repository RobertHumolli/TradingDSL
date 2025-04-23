from lark import Lark, Transformer
from database.database import get_latest_stock_price

# DSL Grammar
dsl_grammar = """
    start: (normal_command | loop_command)+

    normal_command: ACTION QUANTITY? SYMBOL condition?
    loop_command: "for" "symbol" "in" "[" symbol_list "]" condition ACTION QUANTITY?

    symbol_list: SYMBOL ("," SYMBOL)*

    condition: "if" "price" COMPARISON VALUE

    ACTION: "buy" | "sell"
    QUANTITY: /[0-9]+/
    SYMBOL: "AAPL" | "MSFT" | "GOOGL" | "AMZN" | "META" | "NVDA" | "TSLA"
    VALUE: /[0-9]+/
    COMPARISON: ">" | "<" | ">=" | "<=" | "=="

    %import common.WS
    %ignore WS
"""

# Create the DSL parser
dsl_parser = Lark(dsl_grammar, parser="lalr")

# Transformer to convert parse tree into actionable dicts
class TradingTransformer(Transformer):
    def start(self, children):
        return children

    def normal_command(self, children):
        action = children[0]

        if isinstance(children[1], int):
            quantity = children[1]
            symbol = children[2]
            condition = children[3] if len(children) > 3 else None
        else:
            quantity = 1
            symbol = children[1]
            condition = children[2] if len(children) > 2 else None

        return {
            "type": "single",
            "action": action,
            "symbol": symbol.upper(),
            "quantity": quantity,
            "condition": condition
        }

    def loop_command(self, children):
        symbols = children[0]
        condition = children[1]
        action = children[2]

        if len(children) == 4:
            quantity = children[3]
        else:
            quantity = 1

        return {
            "type": "loop",
            "symbols": symbols,
            "action": action,
            "condition": condition,
            "quantity": quantity
        }

    def symbol_list(self, children):
        return [s.upper() for s in children]

    def condition(self, children):
        if len(children) == 2:
            comparison, value = children
            return {
                "comparison": comparison,
                "value": value
            }
        return None

    def ACTION(self, token):
        return token.value

    def QUANTITY(self, token):
        return int(token.value)

    def SYMBOL(self, token):
        return token.value

    def VALUE(self, token):
        return int(token.value)

    def COMPARISON(self, token):
        return token.value

# Execute a command object based on its type, so it can do a single command or a looped command
def execute_command(command):
    if command["type"] == "single":
        _execute_single(command)
    elif command["type"] == "loop":
        for symbol in command["symbols"]:
            single = {
                "type": "single",
                "action": command["action"],
                "symbol": symbol,
                "quantity": command.get("quantity", 1),
                "condition": command["condition"]
            }
            _execute_single(single)

# Executes a single command
def _execute_single(command):
    action = command["action"]
    symbol = command["symbol"]
    quantity = command.get("quantity", 1)
    condition = command.get("condition")

    if quantity is None:
        quantity = 1

    if quantity <= 0:
        print(f"Invalid quantity: {quantity}")
        return

    current_price = get_latest_stock_price(symbol)

    if current_price is None:
        print(f"No price data for {symbol}")
        return

    if condition:
        comparison = condition["comparison"]
        value = condition["value"]

        condition_met = (
            (comparison == ">" and current_price > value) or
            (comparison == "<" and current_price < value) or
            (comparison == ">=" and current_price >= value) or
            (comparison == "<=" and current_price <= value) or
            (comparison == "==" and current_price == value)
        )

        if condition_met:
            print(f"Executing {action} {quantity}x {symbol} at price {current_price}")
        else:
            print(f"Condition not met for {symbol}: price {current_price} is not {comparison} {value}")
    else:
        print(f"Executing {action} {quantity}x {symbol} at price {current_price}")


# Main function that runs the parser and executes the DSL commands
def main():
    while True:
        dsl_input = input("Enter trading command (e.g., 'buy AAPL if price > 150', or 'for symbol in [AAPL, MSFT, TSLA] if price > 150 buy') or 'quit': ")
        if dsl_input.lower() == "quit":
            break
        try:
            tree = dsl_parser.parse(dsl_input)
            commands = TradingTransformer().transform(tree)
            for command in commands:
                execute_command(command)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
