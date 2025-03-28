from lark import Lark, Transformer
from database.database import get_latest_stock_price

# DSL Grammar
dsl_grammar = """
    start: command+

    command: ACTION SYMBOL condition?

    condition: "if" "price" COMPARISON VALUE

    ACTION: "buy" | "sell"

    SYMBOL: "AAPL" | "MSFT" | "GOOGL" | "AMZN" | "META" | "NVDA" | "TSLA"

    VALUE: /[0-9]+/

    COMPARISON: ">" | "<" | ">=" | "<=" | "=="

    %import common.WS
    %ignore WS
"""

# Create the DSL parser using Lark in this instance
dsl_parser = Lark(dsl_grammar, parser="lalr")

class TradingTransformer(Transformer):
    def start(self, children):
        return children

    def command(self, children):
        action, symbol, *condition = children
        command = {
            "action": action,
            "symbol": symbol.upper(),
        }
        if condition:
            command["condition"] = condition[0]
        return command

    def condition(self, children):
        if len(children) == 2:  #This was put in here due to the index of the array constantly being out of range
            comparison, value = children
            return {
                "comparison": comparison,
                "value": value,
            }
        return None  # If there is no condition given, it will allow for the second print statement to be used (finally)

    def ACTION(self, token):
        return token.value

    def SYMBOL(self, token):
        return token.value

    def VALUE(self, token):
        return int(token.value)

    def COMPARISON(self, token):
        return token.value

# Execution function
def execute_command(command):
    action = command["action"]
    symbol = command["symbol"]
    condition = command.get("condition")

    if condition:
        comparison = condition["comparison"]
        value = condition["value"]

        #This will help get the latest stock price for the current stock symbol from the database.
        current_price = get_latest_stock_price(symbol)

        if current_price is None:
            print(f"No price data available for {symbol}")
            return

        #Will state whether the condition is met or not and execute the buy order depending on this.
        if ( 
            (comparison == ">" and current_price > value) or 
            (comparison == "<" and current_price < value) or
            (comparison == ">=" and current_price >= value) or
            (comparison == "<=" and current_price <= value)
        ):
            print(f"Executing {action.upper()} order for {symbol} at current price {current_price}")
        else:
            print(f"Condition not met for {action.upper()} order for {symbol}: current price {current_price} is not {comparison} {value}")
    else:
        print(f"Executing {action.upper()} order for {symbol}")

# Main function that allows the user to input the DSL commands and what they would like to buy/sell
def main():
    while True:
        dsl_input = input("Enter trading command (e.g., 'buy AAPL if price > 150') or 'quit': ")
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