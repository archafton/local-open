# Project Tacitus

Project Tacitus is a comprehensive platform designed to provide users with access to legislative data, voting records, and representative information. By leveraging data from various government sources and applying advanced processing techniques, it aims to make legislative information more accessible and understandable to citizens.

## Project Structure

```
project-tacitus/
├── backend/
│   └── src/
│       ├── python/
│       │   └── congressgov/
│       │       ├── bill_fetch/      # Bill fetching and processing
│       │       ├── bill_summary/    # AI-powered bill summarization
│       │       └── members_fetch/   # Representative data fetching
│       ├── api.py                   # Main API endpoints
│       ├── app.py                   # Application setup
│       └── schema.sql              # Database schema
├── Docs/
│   ├── 1_Project_Overview/         # Project vision and goals
│   ├── 2_Technical_Documentation/  # Implementation details
│   ├── 3_API_Documentation/        # API endpoints and usage
│   └── 4_Deployment_Guides/        # Setup and deployment guides
└── frontend/
    └── src/
        ├── components/             # React components
        ├── pages/                  # Page layouts
        └── styles/                 # CSS styles
```

## Features

### Current Functionality
- Automated bill data fetching and enrichment
- Member data collection and updates
- Representatives viewing and filtering
  - Name search
  - Chamber filter
  - Party filter
  - Leadership role filter
  - State/district filters
- Dark mode support
- Real-time data processing
- Comprehensive error handling and logging

### In Development
- Enhanced bill analysis
- Additional data visualizations
- Advanced search capabilities
- User authentication system

### Planned Features
- Analytics dashboard with voting pattern analysis
- Full-text bill search with advanced filtering
- Customizable user dashboards
- Machine learning integration for predictive analytics

## Technology Stack

### Backend
- **Language**: Python
- **Framework**: Flask API
- **Database**: PostgreSQL
  - Structured tables for bills, members, votes, committees
  - Version control for bill texts and actions
  - Relationship tracking between entities
- **External Integration**: Congress.gov API
- **Data Processing**: AI/LLM for bill summarization

### Frontend
- **Framework**: React
- **Styling**: Tailwind CSS
- **Features**: 
  - Dark mode support
  - Responsive design
  - Real-time data filtering
  - Loading states and error handling
- **State Management**: React Hooks (useState, useEffect)

## Prerequisites

- Python 3.8 or higher
- PostgreSQL
- Node.js and npm
- Git

## Getting Started

1. **Database Setup**
```bash
createdb project_tacitus_test
psql -d project_tacitus_test -f backend/src/schema.sql
```

2. **Environment Setup**
Create a `.env` file in the project root:
```bash
DATABASE_URL=postgresql://localhost/project_tacitus_test
CONGRESSGOV_API_KEY=your_api_key_here  # Get this from api.congress.gov
```

Note: You'll need to register for an API key at api.congress.gov to use this application.

3. **Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 src/api.py
```

4. **Frontend Setup**
```bash
cd frontend
npm install
npm start
```

5. **Database Check**
```bash
psql postgresql://localhost/project_tacitus_test -c "SELECT COUNT(*) FROM bills;"
```

6. **Data Fetching**
```bash
cd backend
source venv/bin/activate
python3 src/python/congressgov/bill_fetch/bill_fetch.py
```

## Documentation

For detailed setup instructions and troubleshooting, see `Docs/4_Deployment_Guides/Local_Test_Environment_Setup.md`.

Additional documentation is available in the `Docs` directory:

- `1_Project_Overview/`: Project vision and goals
- `2_Technical_Documentation/`: Implementation details and architecture
- `3_API_Documentation/`: API endpoints and usage guides
- `4_Deployment_Guides/`: Setup and deployment instructions

## Development and Maintenance

### Local Development Setup
- Local PostgreSQL database for data storage
- Python backend with Flask API
- React frontend for user interface
- AI-powered bill summarization capabilities

### Monitoring
- Error logging and tracking
- Performance monitoring
- API usage statistics
- Database health checks

### Regular Updates
- Data refreshes from Congress.gov
- API version management
- Database migrations
- Security patches

## Contributing

Please refer to the `CONTRIBUTING.md` file for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
