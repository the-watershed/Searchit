"""
AnalyticsPage: Comprehensive analytics dashboard with beautiful formatting and color-coded insights.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
    QFrame, QGridLayout, QProgressBar, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette
from db import DB
import datetime

class AnalyticsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.db = DB()
        self.init_ui()
        self.refresh()

    def init_ui(self):
        # Main layout with scroll area
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with refresh button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 15, 20, 10)
        
        title_label = QLabel("📊 JUREKA! Treasures Analytics Dashboard")
        title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #2b1e1e;
            padding: 10px 0;
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh Data")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #8b5e34;
                color: #f7efe4;
                border: 1px solid #6f482a;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #a66f3c;
            }
        """)
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 10, 20, 20)
        self.content_layout.setSpacing(20)
        self.content_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)

    def create_section_frame(self, title, content_widget):
        """Create a styled frame for each analytics section."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("""
            QFrame {
                background: #efe7d6;
                border: 1px solid #bda77b;
                border-radius: 4px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 15)
        
        # Section title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2b1e1e;
            padding-bottom: 8px;
            border-bottom: 1px solid #bda77b;
            margin-bottom: 10px;
            background: transparent;
        """)
        layout.addWidget(title_label)
        
        # Content
        layout.addWidget(content_widget)
        
        return frame

    def create_metric_widget(self, label, value, color="#2b1e1e", large=False):
        """Create a styled metric display."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Value
        value_label = QLabel(str(value))
        font_size = "20px" if large else "16px"
        value_label.setStyleSheet(f"""
            font-size: {font_size};
            font-weight: bold;
            color: {color};
            background: transparent;
        """)
        layout.addWidget(value_label)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet("""
            font-size: 11px;
            color: #6f482a;
            font-weight: normal;
            background: transparent;
        """)
        layout.addWidget(label_widget)
        
        return widget

    def create_progress_bar(self, value, maximum, color="#8b5e34"):
        """Create a styled progress bar."""
        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(maximum)
        progress.setValue(value)
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #bda77b;
                border-radius: 5px;
                text-align: center;
                height: 20px;
                background-color: #f8f3e7;
                color: #2b1e1e;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        return progress

    def refresh(self):
        """Refresh all analytics data and rebuild the interface."""
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        try:
            # Get comprehensive analytics data
            data = self.db.get_comprehensive_analytics()
            
            # Create analytics sections
            self._create_overview_section(data)
            self._create_collection_breakdown(data)
            self._create_price_analytics(data)
            self._create_activity_section(data)
            self._create_quality_metrics(data)
            self._create_top_performers(data)
            
        except Exception as e:
            error_label = QLabel(f"❌ Error loading analytics: {str(e)}")
            error_label.setStyleSheet("color: #d32f2f; font-size: 14px; padding: 20px;")
            self.content_layout.addWidget(error_label)

    def _create_overview_section(self, data):
        """Create the collection overview section."""
        overview_widget = QWidget()
        layout = QGridLayout(overview_widget)
        layout.setSpacing(15)
        
        # Key metrics
        layout.addWidget(self.create_metric_widget(
            "Total Items", data.get('total_items', 0), "#8B4513", large=True), 0, 0)
        layout.addWidget(self.create_metric_widget(
            "Total Images", data.get('total_images', 0), "#2E7D32", large=True), 0, 1)
        layout.addWidget(self.create_metric_widget(
            "Price Entries", data.get('total_price_entries', 0), "#1976D2", large=True), 0, 2)
        layout.addWidget(self.create_metric_widget(
            "Revisions", data.get('total_revisions', 0), "#7B1FA2", large=True), 0, 3)
        
        # Recent activity
        layout.addWidget(self.create_metric_widget(
            "Added This Month", data.get('items_added_30_days', 0), "#FF6F00"), 1, 0)
        layout.addWidget(self.create_metric_widget(
            "Recent Revisions", data.get('revisions_30_days', 0), "#E65100"), 1, 1)
        
        frame = self.create_section_frame("🏛️ Collection Overview", overview_widget)
        self.content_layout.addWidget(frame)

    def _create_collection_breakdown(self, data):
        """Create collection breakdown by condition, brand, etc."""
        breakdown_widget = QWidget()
        layout = QHBoxLayout(breakdown_widget)
        
        # Condition breakdown
        condition_widget = QWidget()
        condition_layout = QVBoxLayout(condition_widget)
        condition_layout.addWidget(QLabel("By Condition:"))
        
        conditions = data.get('items_by_condition', [])
        condition_colors = ["#4CAF50", "#FF9800", "#F44336", "#9C27B0", "#607D8B"]
        
        for i, (condition, count) in enumerate(conditions[:5]):
            color = condition_colors[i % len(condition_colors)]
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            
            label = QLabel(f"{condition}: {count}")
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
            row_layout.addWidget(label)
            
            condition_layout.addWidget(row_widget)
        
        layout.addWidget(condition_widget)
        
        # Brand breakdown
        brand_widget = QWidget()
        brand_layout = QVBoxLayout(brand_widget)
        brand_layout.addWidget(QLabel("Top Brands:"))
        
        brands = data.get('top_brands', [])
        brand_colors = ["#1976D2", "#388E3C", "#F57C00", "#7B1FA2", "#5D4037"]
        
        for i, (brand, count) in enumerate(brands[:5]):
            color = brand_colors[i % len(brand_colors)]
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            
            label = QLabel(f"{brand}: {count}")
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
            row_layout.addWidget(label)
            
            brand_layout.addWidget(row_widget)
        
        layout.addWidget(brand_widget)
        
        frame = self.create_section_frame("📊 Collection Breakdown", breakdown_widget)
        self.content_layout.addWidget(frame)

    def _create_price_analytics(self, data):
        """Create price analytics section."""
        price_widget = QWidget()
        layout = QVBoxLayout(price_widget)
        
        # Price overview
        overview_layout = QHBoxLayout()
        overview_layout.addWidget(self.create_metric_widget(
            "Minimum Price", f"${data.get('price_min', 0):.2f}", "#4CAF50"))
        overview_layout.addWidget(self.create_metric_widget(
            "Average Price", f"${data.get('price_avg', 0):.2f}", "#FF9800"))
        overview_layout.addWidget(self.create_metric_widget(
            "Maximum Price", f"${data.get('price_max', 0):.2f}", "#F44336"))
        
        layout.addLayout(overview_layout)
        
        # Price distribution
        layout.addWidget(QLabel("Price Distribution:"))
        
        price_dist = data.get('price_distribution', [])
        # Vintage-themed color palette: browns, tans, and warm earth tones
        dist_colors = ["#8b5e34", "#a0683a", "#b4733f", "#c87e45", "#dc8a4b", "#d4975c"]
        
        for i, (range_label, count) in enumerate(price_dist):
            color = dist_colors[i % len(dist_colors)]
            
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 5, 0, 5)
            
            label = QLabel(f"{range_label}")
            label.setFixedWidth(100)
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
            row_layout.addWidget(label)
            
            progress = self.create_progress_bar(count, max([c for _, c in price_dist]), color)
            row_layout.addWidget(progress)
            
            count_label = QLabel(f"{count}")
            count_label.setFixedWidth(40)
            count_label.setAlignment(Qt.AlignRight)
            row_layout.addWidget(count_label)
            
            layout.addWidget(row_widget)
        
        frame = self.create_section_frame("💰 Price Analytics", price_widget)
        self.content_layout.addWidget(frame)

    def _create_activity_section(self, data):
        """Create activity timeline section."""
        activity_widget = QWidget()
        layout = QVBoxLayout(activity_widget)
        
        layout.addWidget(QLabel("Monthly Activity (Last 12 Months):"))
        
        monthly_data = data.get('monthly_activity', [])
        if monthly_data:
            max_items = max([count for _, count in monthly_data])
            
            for month, count in monthly_data:
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 3, 0, 3)
                
                # Month label
                try:
                    month_obj = datetime.datetime.strptime(month, '%Y-%m')
                    month_label = month_obj.strftime('%B %Y')
                except:
                    month_label = month
                
                label = QLabel(month_label)
                label.setFixedWidth(120)
                label.setStyleSheet("font-weight: bold; color: #1976D2;")
                row_layout.addWidget(label)
                
                # Progress bar
                progress = self.create_progress_bar(count, max_items, "#1976D2")
                row_layout.addWidget(progress)
                
                # Count
                count_label = QLabel(f"{count}")
                count_label.setFixedWidth(40)
                count_label.setAlignment(Qt.AlignRight)
                row_layout.addWidget(count_label)
                
                layout.addWidget(row_widget)
        
        frame = self.create_section_frame("📈 Activity Timeline", activity_widget)
        self.content_layout.addWidget(frame)

    def _create_quality_metrics(self, data):
        """Create data quality metrics section."""
        quality_widget = QWidget()
        layout = QVBoxLayout(quality_widget)
        
        total_items = data.get('total_items', 1)  # Avoid division by zero
        
        # Data completeness metrics
        metrics = [
            ("Items with Titles", data.get('items_with_title', 0), "#4CAF50"),
            ("Items with Descriptions", data.get('items_with_description', 0), "#2196F3"),
            ("Items with Provenance", data.get('items_with_provenance', 0), "#FF9800"),
        ]
        
        for label, count, color in metrics:
            percentage = (count / total_items) * 100 if total_items > 0 else 0
            
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 5, 0, 5)
            
            metric_label = QLabel(label)
            metric_label.setFixedWidth(180)
            metric_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            row_layout.addWidget(metric_label)
            
            progress = self.create_progress_bar(int(percentage), 100, color)
            row_layout.addWidget(progress)
            
            percent_label = QLabel(f"{percentage:.1f}%")
            percent_label.setFixedWidth(50)
            percent_label.setAlignment(Qt.AlignRight)
            row_layout.addWidget(percent_label)
            
            layout.addWidget(row_widget)
        
        # Text length metrics
        layout.addWidget(QLabel("\nAverage Text Lengths:"))
        
        text_metrics = [
            ("Title Length", data.get('avg_title_length', 0)),
            ("Description Length", data.get('avg_description_length', 0)),
            ("Notes Length", data.get('avg_notes_length', 0)),
        ]
        
        for label, length in text_metrics:
            metric_widget = self.create_metric_widget(label, f"{length:.1f} chars", "#666")
            layout.addWidget(metric_widget)
        
        frame = self.create_section_frame("📋 Data Quality", quality_widget)
        self.content_layout.addWidget(frame)

    def _create_top_performers(self, data):
        """Create top performers section."""
        performers_widget = QWidget()
        layout = QHBoxLayout(performers_widget)
        
        # Most documented items
        documented_widget = QWidget()
        documented_layout = QVBoxLayout(documented_widget)
        documented_layout.addWidget(QLabel("Most Documented Items:"))
        
        most_documented = data.get('most_documented_items', [])
        for i, (title, brand, img_count) in enumerate(most_documented[:5]):
            color = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#607D8B"][i]
            label = QLabel(f"{title[:30]}{'...' if len(title) > 30 else ''} ({img_count} images)")
            label.setStyleSheet(f"color: {color}; font-size: 11px; padding: 2px;")
            documented_layout.addWidget(label)
        
        layout.addWidget(documented_widget)
        
        # Most revised items
        revised_widget = QWidget()
        revised_layout = QVBoxLayout(revised_widget)
        revised_layout.addWidget(QLabel("Most Revised Items:"))
        
        most_revised = data.get('most_revised_items', [])
        for i, (title, brand, rev_count) in enumerate(most_revised[:5]):
            # Vintage-themed colors for top performers
            color = ["#8b5e34", "#a0683a", "#b4733f", "#c87e45", "#dc8a4b"][i]
            label = QLabel(f"{title[:30]}{'...' if len(title) > 30 else ''} ({rev_count} revisions)")
            label.setStyleSheet(f"color: {color}; font-size: 11px; padding: 2px; background: transparent;")
            revised_layout.addWidget(label)
        
        layout.addWidget(revised_widget)
        
        frame = self.create_section_frame("🏆 Top Performers", performers_widget)
        self.content_layout.addWidget(frame)

