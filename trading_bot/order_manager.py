import json
import os
from datetime import datetime

class OrderManager:
    def __init__(self, prefix=''):
        # Criar diretório para salvar as ordens
        os.makedirs("data", exist_ok=True)
        
        # Gerar nome do arquivo com timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix_str = f"{prefix}_" if prefix else ""
        self.orders_file = f"data/{prefix_str}orders_{self.timestamp}.json"
        self._initialize_file()

    def _initialize_file(self):
        """Initialize orders file if it doesn't exist"""
        if not os.path.exists(self.orders_file):
            with open(self.orders_file, 'w') as f:
                json.dump([], f)

    def _load_orders(self):
        """Load orders from JSON file"""
        try:
            with open(self.orders_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def save_order(self, order):
        """Save a new order to JSON file"""
        orders = self._load_orders()
        
        # Add timestamp and format order
        formatted_order = {
            'order_id': order['orderId'],
            'symbol': order['symbol'],
            'side': order['side'],
            'quantity': float(order['executedQty']),
            'price': float(order['cummulativeQuoteQty']) / float(order['executedQty']),
            'timestamp': datetime.now().isoformat(),
            'status': order['status']
        }
        
        orders.append(formatted_order)
        
        with open(self.orders_file, 'w') as f:
            json.dump(orders, f, indent=4)

    def get_last_order(self):
        """Return the last executed order"""
        orders = self._load_orders()
        return orders[-1] if orders else None

    def get_all_orders(self):
        """Return all orders"""
        return self._load_orders() 