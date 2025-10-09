# 🚢 TAURO PROJECT - Maritime Report Analysis System

## 🎯 **Project Overview**
TAURO is an **intelligent maritime report analysis system** designed to automate the processing of maritime inspection reports. It extracts, analyzes, and provides intelligent insights from Excel-based maritime reports through a modern web interface and specialized AI chatbot.

### **🎯 Main Objectives:**
- **Automate extraction** of maritime inspection data from Excel reports
- **Provide intelligent analysis** of operational events and conditions
- **Offer specialized chatbot** for specific queries
- **Support bilingual operations** (Spanish/English)
- **Modern web interface** for maritime inspectors

---

## 🏗️ **System Architecture**

### **📊 Complete Data Flow:**
```
Excel File → Cellmap → Header + Events + Notes → Analysis → Complete Chatbot
    ↓         ↓         ↓         ↓         ↓         ↓
[create_  [extract_  [extract_  [extract_  [basic_  [maritime_
cellmap]  header]   timesheet] notes]    analyzer] chatbot]
```

### **🔄 Complete Integration:**
- **Header**: General report data (vessels, products, references)
- **Events**: Chronological TIME LOG of inspector events
- **Notes**: Operational data specific to each timesheet
- **Chatbot**: Complete context with access to ALL information

### **🔄 Step-by-Step Process:**

#### **1. Input:**
- **User**: Drags Excel file (.xlsx/.xlsm)
- **Content**: Maritime inspector reports
- **Languages**: Mixed Spanish and English

#### **2. Extraction (Processing):**
- **`create_cellmap.py`**: Excel → JSON with all cells
- **`extract_report_header.py`**: JSON → Report header data
- **`extract_timesheet_events.py`**: JSON → Chronological TIME LOG events
- **`extract_operational_notes.py`**: JSON → Complete operational notes:
  - Specific header for each timesheet (Vessel, Terminal, Location, Product, Date, File N°)
  - Pumping data (Pumping Time, Pumping Rate) from General Notes
  - Weather and sea conditions from Special Notes
  - Additional information (Last Cargo, Vessel Experience Factor)
- **Result**: Complete maritime report context

#### **3. Analysis:**
- **`basic_analyzer.py`**: Events → Professional report
- **Categorization**: Lightering, Loading, Inspection, etc.
- **Result**: Complete analysis with recommendations

#### **4. Interaction:**
- **`maritime_chatbot.py`**: Chatbot specialized in COMPLETE MARITIME REPORTS
- **AI**: OpenAI GPT-4o-mini with integral context
- **Capabilities**:
  - Complete access to TIME LOG (detailed chronological events)
  - Specific information for each vessel and timesheet
  - Pumping data with correct units (m³/h, hours)
  - Operational conditions (weather and maritime)
  - Bilingual context (Spanish/English)
- **Result**: Precise answers about any aspect of the report

#### **5. Presentation (Frontend):**
- **`app.py`**: Flask web server
- **`index.html`**: Dark theme web interface
- **`app.js`**: Interactivity and communication
- **`style.css`**: Modern and responsive design

---

## 📁 **File Structure**

### **🐍 Python Backend:**
```
📂 Tauro/
├── 🚀 run.py                    # System entry point
├── 🌐 app.py                    # Flask web server (REST API)
├── 🗺️ create_cellmap.py         # Excel cell extractor
├── 📋 extract_report_header.py  # Header data extractor
├── ⏰ extract_timesheet_events.py # Chronological events extractor  
├── 📝 extract_operational_notes.py # Operational notes extractor
├── 📊 basic_analyzer.py         # Automatic analyzer without AI
├── 🤖 maritime_chatbot.py       # Specialized maritime chatbot
└── ⚙️ .env                      # Configuration (API keys, etc.)
```

### **🌐 Web Frontend:**
```
📂 templates/
└── 🏠 index.html               # Main web page

📂 static/
├── 📂 css/
│   └── 🎨 style.css            # Dark theme styles
└── 📂 js/
    └── ⚡ app.js               # Interactive JavaScript
```

### **📊 Data and Results:**
```
📂 uploads/                     # Uploaded Excel files
📂 output/                      # Processed results
├── file_cellmap.json          # Complete extracted cell map
├── file_header.json           # Report header data
├── file_events.json           # Chronological TIME LOG events
├── file_notes.json            # Complete operational notes:
│                               #   - Specific sheet header
│                               #   - Pumping data (General Notes)
│                               #   - Weather conditions (Special Notes)
└── file_analysis.json         # Generated analysis
```

---

## 🔧 **Technologies Used**

### **Backend:**
- **🐍 Python 3.8+**: Main language
- **🌐 Flask**: Web framework for REST API
- **📊 OpenPyXL**: Excel file processing
- **🤖 OpenAI GPT-4o-mini**: Artificial intelligence for chatbot
- **📝 JSON**: Structured data storage

### **Frontend:**
- **🌐 HTML5**: Modern web structure
- **🎨 CSS3**: Dark theme styling
- **⚡ JavaScript**: Dynamic interactivity
- **📱 Responsive Design**: Adapts to mobile and tablets

### **Infrastructure:**
- **🔄 REST API**: Communication between frontend and backend
- **📁 File System**: Local storage for uploads and results
- **🌍 Web Server**: Flask development server

---

## 🚀 **Key Features**

### **1. 📊 Intelligent Extraction**
- **Automatic detection**: Finds timesheets automatically
- **Bilingual support**: Recognizes terms in Spanish and English
- **Dynamic structure**: Adapts to different report formats
- **Complete data**: Header + Events + Operational Notes

### **2. ⏰ Chronological Events**
- **Intelligent detection**: Finds timesheets automatically
- **Chronological events**: Date, time, structured description
- **Bilingual**: Recognizes terms in Spanish and English

### **3. 📊 Automatic Analysis**
- **Categorization**: Lightering, Loading, Unloading, Inspection, etc.
- **Temporal analysis**: Duration, sequence, critical events
- **Recommendations**: Based on maritime best practices
- **Professional report**: Structured and readable format

### **4. 🤖 Intelligent Chatbot - COMPLETE MARITIME REPORTS**
- **Specialized**: Knows bilingual maritime terminology
- **Integral Context**: Complete access to:
  - 📋 Report header data
  - ⏰ Complete chronological TIME LOG (detailed events)
  - 📝 Operational notes specific to each sheet
  - 🚢 Specific information for each vessel
- **Advanced Capabilities**:
  - Understands that TIME LOG = EVENTS (same chronological record)
  - Pumping data with correct units (m³/h, hours)
  - Operational conditions (weather and maritime)
  - Specific information per vessel and timesheet
- **Conversational**: Maintains chat history
- **Bilingual**: Responds in Spanish or English automatically
- **Precision**: Never says "I don't have details" - has complete access

### **5. 🌐 Web Interface**
- **Dark Theme**: Reduces visual fatigue
- **Responsive**: Adapts to mobile and tablets
- **Intuitive**: Easy to use for inspectors
- **Modern**: Smooth animations and effects
- **Professional**: Appropriate design for industry
- **Streamlined**: Focus on core functionality without file history distractions

---

## 🔄 **Recent Updates**

### **🎯 STREAMLINED INTERFACE (October 2025):**
- **Removed file history**: Eliminated "Recently Processed Files" section for cleaner interface
- **Focused workflow**: Direct upload → process → analyze → chat workflow
- **Reduced complexity**: Removed unnecessary file management features
- **Better UX**: Cleaner, more focused user experience

### **🚀 COMPLETE OPERATIONAL NOTES INTEGRATION (October 2025):**
- **New component**: `extract_operational_notes.py` for extracting operational data
- **Extracted data**:
  - Specific header for each timesheet (Vessel, Terminal, Location, Product, Date, File N°)
  - Pumping data (Pumping Time, Pumping Rate) with correct units
  - Weather and maritime conditions (Special Notes)
  - Additional information (Last Cargo, Vessel Experience Factor)
- **Improved chatbot**: Complete context with access to ALL information
- **Problem solved**: Chatbot no longer says "I don't have details" - has complete access
- **Result**: Fully integrated system with complete maritime context

### **✅ Critical Chatbot Correction (October 2025):**
- **Problem identified**: Chatbot didn't include "Revised by" and "Approved by" fields in its context
- **Solution implemented**: System prompt update to include all operational data
- **Result**: Chatbot now correctly answers questions about report revision and approval
- **Impact**: Complete functionality for maritime report traceability

### **🎯 Validated Capabilities:**
- ✅ **"Who was the inspector?"** → Correct answer
- ✅ **"Who reviewed it?"** → Correct answer (fixed)
- ✅ **"Who approved it?"** → Correct answer (fixed)
- ✅ **"What was the first recorded task?"** → Specific TIME LOG event
- ✅ **"Which vessel has pumping data?"** → Specific sheet information
- ✅ **"What were the weather conditions?"** → Special Notes (clear, calm, etc.)
- ✅ **"What was the pumping time?"** → General Notes with units (hours)
- ✅ **"What was the pumping rate?"** → General Notes with units (m³/h)
- ✅ **"At which terminal was it performed?"** → Specific sheet header
- ✅ **"Give me TIME LOG details"** → Complete chronological events
- ✅ **"Give me a complete summary"** → Integration of all information
- ✅ **Dynamic extraction**: No hardcoded names
- ✅ **Variation handling**: "Inspector" vs "Surveyor"

---

## 🚀 **Future Roadmap**

### **📋 Upcoming Features:**
- **Database**: PostgreSQL for persistent storage
- **Multiple users**: Authentication system
- **Advanced reports**: PDF and Word export
- **Real-time notifications**: WebSocket integration
- **Mobile app**: Native iOS and Android applications

### **🔧 Technical Improvements:**
- **Performance optimization**: Caching and indexing
- **Advanced AI**: Fine-tuned models for maritime domain
- **Integration**: APIs with maritime management systems
- **Security**: Advanced encryption and audit

---

## 🎯 **Project Benefits**

### **⚡ For Maritime Inspectors:**
- **Time saving**: Automated analysis instead of manual review
- **Error reduction**: Consistent and precise extraction
- **Intelligent insights**: AI-powered recommendations
- **Easy access**: Modern and intuitive web interface
- **Bilingual support**: Works with international reports

### **🏢 For Maritime Companies:**
- **Process standardization**: Consistent analysis across all reports
- **Operational efficiency**: Faster report processing
- **Quality improvement**: Detailed analysis and recommendations
- **Cost reduction**: Less manual work required
- **Regulatory compliance**: Complete and traceable reports

### **🌍 For the Maritime Industry:**
- **🔍 Artificial intelligence** for data processing
- **🌐 Modern web interface** for ease of use
- **🤖 Specialized chatbot** for specific queries
- **📊 Professional analysis** without manual intervention
- **🌍 Bilingual support** for international operations

---

## 🛠️ **Installation and Setup**

### **📋 Requirements:**
- Python 3.8+
- OpenAI API Key
- Modern web browser

### **🚀 Quick Start:**
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` file with your OpenAI API key
4. Run: `python run.py`
5. Open browser at `http://localhost:5000`

### **📁 Upload and Process:**
1. Drag Excel file to the web interface
2. Wait for automatic processing (cellmap → header → events → notes)
3. Use the specialized chatbot to query the data
4. Get intelligent insights about maritime operations

---

**TAURO Project - Transforming maritime report analysis through artificial intelligence** 🚢⚡📊
