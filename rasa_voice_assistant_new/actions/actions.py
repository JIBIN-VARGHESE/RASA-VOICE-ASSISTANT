import sqlite3
from typing import Any, Text, Dict, List, Tuple
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ValidateFinancialInfoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_financial_info_form"

    async def validate_year(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        logger.debug(f"Validating year: {slot_value}")
        # Add validation logic here if needed
        return {"year": slot_value}

    async def validate_metric(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        logger.debug(f"Validating metric: {slot_value}")
        # Add validation logic here if needed
        return {"metric": slot_value}

    async def validate_quarter(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        logger.debug(f"Validating quarter: {slot_value}")
        # Quarter is optional, so we just return it as is
        return {"quarter": slot_value}

    async def validate_submetric(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        logger.debug(f"Validating submetric: {slot_value}")
        # Submetric is optional, so we just return it as is
        return {"submetric": slot_value}


class ActionQueryDatabase(Action):
    def name(self) -> Text:
        return "action_query_database"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        logger.debug("Running action_query_database")
        year = tracker.get_slot("year")
        quarter = tracker.get_slot("quarter")
        metric = tracker.get_slot("metric")

        logger.debug(f"Slots: year={year}, quarter={quarter}, metric={metric}")

        if not year:
            dispatcher.utter_message(template="utter_ask_year")
            return [SlotSet("requested_slot", "year")]
        if not metric:
            dispatcher.utter_message(template="utter_ask_metric")
            return [SlotSet("requested_slot", "metric")]

        normalized_metric, submetric = self.normalize_metric_name(metric)
        query_result = self.query_database(year, quarter, normalized_metric, submetric)
        response = self.format_response(
            query_result, year, quarter, normalized_metric, submetric
        )
        dispatcher.utter_message(response)

        return []

    def query_database(
        self, year: Text, quarter: Text, metric: Text, submetric: Text
    ) -> Dict:
        conn = sqlite3.connect("financial_data.db")
        cursor = conn.cursor()

        if quarter:
            query = "SELECT * FROM financial_results WHERE year=? AND quarter=?"
            cursor.execute(query, (year, quarter.lower()))
        else:
            query = "SELECT * FROM financial_results WHERE year=? ORDER BY quarter"
            cursor.execute(query, (year,))

        results = cursor.fetchall()
        conn.close()
        return {"results": results, "metric": metric, "submetric": submetric}

    def format_response(
        self, data: Dict, year: Text, quarter: Text, metric: Text, submetric: Text
    ) -> Text:
        if not data["results"]:
            return f"Sorry, I couldn't find the financial information for {year}{' ' + quarter.upper() if quarter else ''}."

        response = f"Financial details for {year}"
        response += f" {quarter.upper()}" if quarter else ""
        response += f":\n\n"

        total = 0

        if metric.lower() == "revenue":
            if submetric:
                submetric_index = self.get_submetric_index(submetric)
                for result in data["results"]:
                    revenue_query = (
                        "SELECT * FROM revenue_details WHERE financial_result_id=?"
                    )
                    cursor = sqlite3.connect("financial_data.db").cursor()
                    cursor.execute(revenue_query, (result[0],))
                    revenue_data = cursor.fetchone()

                    value = revenue_data[submetric_index]
                    response += f"{result[2].upper()}: {value}\n"
                    total += value

                response += f"\nTotal {submetric} revenue for {year}: {total}\n"
            else:
                for result in data["results"]:
                    revenue_query = (
                        "SELECT * FROM revenue_details WHERE financial_result_id=?"
                    )
                    cursor = sqlite3.connect("financial_data.db").cursor()
                    cursor.execute(revenue_query, (result[0],))
                    revenue_data = cursor.fetchone()

                    quarter_total = sum(revenue_data[1:])  # Sum all revenue sub-metrics
                    response += f"{result[2].upper()}:\n"
                    for i, submetric in enumerate(self.get_revenue_submetrics()):
                        response += f"  {submetric}: {revenue_data[i+1]}\n"
                    response += f"  Quarter Total: {quarter_total}\n\n"
                    total += quarter_total

                response += f"Total Revenue for {year}: {total}\n"
        else:
            metric_index = self.get_metric_index(metric)
            for result in data["results"]:
                value = result[metric_index]
                response += f"{result[2].upper()}: {value}\n"
                total += value

            if not quarter:
                response += f"\nTotal {metric} for {year}: {total}\n"

        return response

    def get_metric_index(self, metric: Text) -> int:
        metric_map = {
            "netProfit": 3,
            "ebita": 4,
            "availableCash": 5,
            "netDebt": 6,
            "revenue": -1,
        }
        return metric_map.get(metric.lower(), -1)

    def get_revenue_submetrics(self):
        return [
            "LargeEnterprise",
            "MidMarketEnterprise",
            "PublicSector",
            "Wholesale",
            "InternationalAndOther",
            "BusinessSegmentRevenue",
            "MassMarketsSegmentRevenue",
        ]

    def get_submetric_index(self, submetric: Text) -> int:
        submetrics = [
            "LargeEnterprise",
            "MidMarketEnterprise",
            "PublicSector",
            "Wholesale",
            "InternationalAndOther",
            "BusinessSegmentRevenue",
            "MassMarketsSegmentRevenue",
        ]
        return submetrics.index(submetric) + 1

    def normalize_metric_name(self, metric: Text) -> Tuple[Text, Text]:
        metric = metric.lower().replace(" ", "")

        # Main metrics
        main_metrics = {
            "netprofit": "netProfit",
            "profit": "netProfit",
            "ebita": "ebita",
            "ebitda": "ebita",
            "availablecash": "availableCash",
            "cash": "availableCash",
            "netdebt": "netDebt",
            "debt": "netDebt",
            "revenue": "revenue",
            "income": "revenue",
            "earnings": "revenue",
        }

        # Revenue submetrics
        revenue_submetrics = {
            "largeenterprise": "LargeEnterprise",
            "midmarketenterprise": "MidMarketEnterprise",
            "publicsector": "PublicSector",
            "wholesale": "Wholesale",
            "internationalandother": "InternationalAndOther",
            "businesssegment": "BusinessSegmentRevenue",
            "massmarketssegment": "MassMarketsSegmentRevenue",
        }

        # Check for main metrics
        for key, value in main_metrics.items():
            if key in metric:
                return value, None

        # Check for revenue submetrics
        for key, value in revenue_submetrics.items():
            if key in metric:
                return "revenue", value

        # If no match found, return the original input
        return metric, None
