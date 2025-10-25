#!/usr/bin/env python3
"""
Demo script for the Insights Service

This script demonstrates how to use the SurfSense Insights Service to:
1. Preview recent document activity
2. Generate insights and actionable plans

Prerequisites:
- SurfSense backend running (default: http://localhost:8002)
- Valid JWT token
- Search space with documents
"""

import argparse
import json
import sys
from datetime import datetime

import requests


class InsightsDemo:
    """Demo client for the Insights Service."""

    def __init__(self, base_url: str, token: str):
        """
        Initialize the demo client.

        Args:
            base_url: Base URL of the SurfSense backend
            token: JWT authentication token
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def preview_activity(self, search_space_id: int, num_documents: int = 30):
        """
        Preview recent document activity.

        Args:
            search_space_id: ID of the search space
            num_documents: Number of documents to preview

        Returns:
            dict: Preview response
        """
        url = f"{self.base_url}/api/v1/insights/preview/{search_space_id}"
        params = {"num_documents": num_documents}

        print(f"\n🔍 Previewing activity for search space {search_space_id}...")
        print(f"   Fetching up to {num_documents} recent documents...\n")

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            self._print_preview(data)
            return data

        except requests.exceptions.HTTPError as e:
            print(f"❌ Error: {e}")
            if e.response.status_code == 404:
                print("   No documents found in this search space.")
            elif e.response.status_code == 403:
                print("   You don't have permission to access this search space.")
            else:
                print(f"   Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None

    def generate_insights(
        self,
        search_space_id: int,
        num_documents: int = 50,
        include_connectors: bool = True,
        include_files: bool = True,
    ):
        """
        Generate insights and planning.

        Args:
            search_space_id: ID of the search space
            num_documents: Number of documents to analyze
            include_connectors: Include connector documents
            include_files: Include file documents

        Returns:
            dict: Insights response
        """
        url = f"{self.base_url}/api/v1/insights/generate"
        payload = {
            "search_space_id": search_space_id,
            "num_documents": num_documents,
            "include_connectors": include_connectors,
            "include_files": include_files,
        }

        print(f"\n🤖 Generating insights for search space {search_space_id}...")
        print(f"   Analyzing {num_documents} documents...")
        print(f"   Include connectors: {include_connectors}")
        print(f"   Include files: {include_files}")
        print("   This may take a few seconds...\n")

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            self._print_insights(data)
            return data

        except requests.exceptions.HTTPError as e:
            print(f"❌ Error: {e}")
            if e.response.status_code == 404:
                print("   No documents found or search space doesn't exist.")
            elif e.response.status_code == 403:
                print("   You don't have permission to access this search space.")
            elif e.response.status_code == 500:
                print("   Server error. Check if LLM is configured properly.")
                print(f"   Response: {e.response.text}")
            else:
                print(f"   Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None

    def _print_preview(self, data: dict):
        """Print preview data in a formatted way."""
        print("=" * 70)
        print("📊 DOCUMENT ACTIVITY PREVIEW")
        print("=" * 70)

        print(f"\n✅ Found {data['total_documents_found']} documents\n")

        insights = data.get("insights_preview", {})
        print("📝 Quick Summary:")
        print(f"   {insights.get('summary', 'N/A')}\n")

        print("🏷️  Key Topics:")
        topics = insights.get("key_topics", [])
        if topics:
            for topic in topics:
                print(f"   • {topic}")
        else:
            print("   No topics extracted")
        print()

        print("📂 Document Type Breakdown:")
        breakdown = insights.get("document_type_breakdown", {})
        if breakdown:
            for doc_type, count in breakdown.items():
                emoji = self._get_doc_type_emoji(doc_type)
                print(f"   {emoji} {doc_type}: {count}")
        else:
            print("   No breakdown available")
        print()

        print("📄 Recent Documents (sample):")
        docs = data.get("documents_preview", [])
        for i, doc in enumerate(docs[:5], 1):  # Show first 5
            print(f"\n   [{i}] {doc['title']}")
            print(f"       Type: {doc['type']}")
            print(f"       Created: {doc['created_at']}")
            preview = doc.get("content_preview", "")
            if preview:
                print(f"       Preview: {preview[:100]}...")

        print("\n" + "=" * 70)
        print(f"💡 {data.get('message', '')}")
        print("=" * 70 + "\n")

    def _print_insights(self, data: dict):
        """Print insights data in a formatted way."""
        print("=" * 70)
        print("🎯 ACTIVITY INSIGHTS & STRATEGIC PLAN")
        print("=" * 70)

        # Print insights
        insights = data.get("insights", {})
        print("\n📊 Activity Summary:")
        print(f"   {insights.get('summary', 'N/A')}\n")

        print("🏷️  Key Topics Identified:")
        topics = insights.get("key_topics", [])
        if topics:
            for topic in topics[:10]:  # Show top 10
                print(f"   • {topic}")
        else:
            print("   No topics identified")
        print()

        print("📂 Document Activity by Type:")
        activity = insights.get("connector_activity", {})
        if activity:
            for doc_type, count in sorted(
                activity.items(), key=lambda x: x[1], reverse=True
            ):
                emoji = self._get_doc_type_emoji(doc_type)
                bar = "█" * min(count, 30)  # Visual bar
                print(f"   {emoji} {doc_type:30s} {bar} {count}")
        print()

        # Print plan
        plan = data.get("plan", {})
        print("=" * 70)
        print(f"📋 PLAN: {plan.get('title', 'N/A')}")
        print("=" * 70)
        print(f"\n{plan.get('description', 'N/A')}\n")
        print(f"⏱️  Estimated timeframe: {plan.get('estimated_timeframe', 'N/A')}\n")

        print("✅ Action Items:")
        action_items = plan.get("action_items", [])
        if action_items:
            for i, item in enumerate(action_items, 1):
                priority = item.get("priority", "MEDIUM")
                priority_emoji = self._get_priority_emoji(priority)

                print(f"\n   {i}. {priority_emoji} {item.get('title', 'N/A')}")
                print(f"      Priority: {priority}")
                print(f"      {item.get('description', 'N/A')}")
                print(f"      💡 Why: {item.get('rationale', 'N/A')}")
        else:
            print("   No action items generated")

        # Print metadata
        metadata = data.get("metadata", {})
        print("\n" + "=" * 70)
        print("ℹ️  Analysis Metadata:")
        print(f"   Documents analyzed: {metadata.get('documents_analyzed', 'N/A')}")
        print(f"   Timestamp: {metadata.get('analysis_timestamp', 'N/A')}")
        print("=" * 70 + "\n")

    def _get_doc_type_emoji(self, doc_type: str) -> str:
        """Get emoji for document type."""
        emoji_map = {
            "SLACK_CONNECTOR": "💬",
            "NOTION_CONNECTOR": "📓",
            "GITHUB_CONNECTOR": "💻",
            "GOOGLE_GMAIL_CONNECTOR": "📧",
            "GOOGLE_CALENDAR_CONNECTOR": "📅",
            "JIRA_CONNECTOR": "📋",
            "CONFLUENCE_CONNECTOR": "📚",
            "FILE": "📄",
            "CLICKUP_CONNECTOR": "✅",
            "LINEAR_CONNECTOR": "🔄",
            "DISCORD_CONNECTOR": "🎮",
            "AIRTABLE_CONNECTOR": "🗃️",
            "LUMA_CONNECTOR": "🎫",
        }
        return emoji_map.get(doc_type, "📄")

    def _get_priority_emoji(self, priority: str) -> str:
        """Get emoji for priority level."""
        emoji_map = {
            "HIGH": "🔴",
            "MEDIUM": "🟡",
            "LOW": "🟢",
        }
        return emoji_map.get(priority, "⚪")


def main():
    """Main entry point for the demo script."""
    parser = argparse.ArgumentParser(
        description="Demo script for SurfSense Insights Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview activity
  python demo_insights.py preview --search-space-id 1 --token YOUR_JWT_TOKEN
  
  # Generate full insights and plan
  python demo_insights.py generate --search-space-id 1 --token YOUR_JWT_TOKEN
  
  # Generate insights for only connector documents
  python demo_insights.py generate --search-space-id 1 --token YOUR_JWT_TOKEN --no-files
  
  # Generate insights for more documents
  python demo_insights.py generate --search-space-id 1 --token YOUR_JWT_TOKEN --num-docs 100
        """,
    )

    parser.add_argument(
        "action",
        choices=["preview", "generate"],
        help="Action to perform: preview or generate",
    )
    parser.add_argument(
        "--search-space-id",
        type=int,
        required=True,
        help="ID of the search space to analyze",
    )
    parser.add_argument(
        "--token", required=True, help="JWT authentication token"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8002",
        help="Base URL of SurfSense backend (default: http://localhost:8002)",
    )
    parser.add_argument(
        "--num-docs",
        type=int,
        default=50,
        help="Number of documents to analyze (default: 50)",
    )
    parser.add_argument(
        "--no-connectors",
        action="store_true",
        help="Exclude connector documents",
    )
    parser.add_argument(
        "--no-files", action="store_true", help="Exclude file documents"
    )

    args = parser.parse_args()

    # Validate options
    if args.no_connectors and args.no_files:
        print("❌ Error: Cannot exclude both connectors and files")
        sys.exit(1)

    # Create demo client
    demo = InsightsDemo(base_url=args.base_url, token=args.token)

    # Execute action
    if args.action == "preview":
        result = demo.preview_activity(
            search_space_id=args.search_space_id, num_documents=args.num_docs
        )
    else:  # generate
        result = demo.generate_insights(
            search_space_id=args.search_space_id,
            num_documents=args.num_docs,
            include_connectors=not args.no_connectors,
            include_files=not args.no_files,
        )

    # Exit with appropriate code
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
