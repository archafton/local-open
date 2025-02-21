# Project Tacitus: Technical Overview

## Project Description
Project Tacitus is a full-stack web application designed to fetch, store, analyze, and visualize legislative data from Congress.gov and other sources. The system provides detailed information about bills, congressional members, voting records, legislative activities, campaign finances, lobbying activity, and government spending activity.

## Technical Stack

### Backend
- **Language**: Python
- **Framework**: Flask
- **API Integration**: Congress.gov API
- **Database**: PostgreSQL

### Frontend
- **Framework**: React
- **Styling**: Tailwind CSS
- **Features**: Dark mode support, responsive design
- **State Management**: React Hooks (useState, useEffect)

## System Architecture

### Data Pipeline
1. **Data Fetching**
   - `bill_fetch.py`: Initial bill data collection
   - `member_fetch.py`: Congressional member data collection
   - `bill_enrichment.py`: Enhanced bill data processing
     - Fetches detailed bill information
     - Processes related bills
     - Handles text versions
     - Manages bill actions and cosponsors

2. **Data Storage**
   - PostgreSQL database with comprehensive schema
   - Structured tables for bills, members, votes, committees
   - Relationship tracking between entities
   - Version control for bill texts and actions

3. **API Layer**
   - RESTful API endpoints using Flask
   - CORS support for frontend integration
   - Efficient database queries
   - JSON response formatting

### Frontend Architecture
1. **Component Structure**
   - Layout component for consistent UI
   - Themed components using ThemeContext
   - Reusable components for tables and filters
   - Responsive design implementation

2. **Features**
   - Representatives view with advanced filtering
   - Real-time data filtering
   - Loading states and error handling
   - Responsive table layouts
   - Dark mode support

## Database Schema

### Core Tables
1. **bills**
   - Basic bill information
   - Relationships to sponsors
   - Text versions and summaries
   - Status tracking
   - Related bills linking

2. **members**
   - Comprehensive member information
   - Biographical data
   - Current role and status
   - Contact information
   - Voting statistics

3. **member_terms**
   - Historical term tracking
   - Chamber assignments
   - Party affiliations
   - State/district representation

4. **votes**
   - Voting record management
   - Bill-member relationships
   - Vote types and dates
   - Vote statistics

### Supporting Tables
- **committees**: Committee information
- **bill_committees**: Bill-committee relationships
- **bill_actions**: Detailed bill activity tracking
- **bill_cosponsors**: Cosponsor management
- **bill_subjects**: Subject matter categorization
- **sponsored_legislation**: Primary sponsorship tracking
- **cosponsored_legislation**: Cosponsor relationship management

## Current Functionality

### Data Management
- Automated bill data fetching and enrichment
- Member data collection and updates
- Real-time data processing
- Comprehensive error handling and logging

### User Interface
- Representatives viewing and filtering
  - Name search
  - Chamber filter
  - Party filter
  - Leadership role filter
  - State/district filters
- Responsive table displays
- Loading state management
- Dark mode support

### API Endpoints
- `/api/representatives`: Current congressional member data
  - Filters current members
  - Returns comprehensive member details
  - Supports frontend filtering operations

## Development Status

### Current Features (Local Development)
- Database schema implementation
- Data fetching infrastructure
- Basic API endpoints
- Representatives view with filtering
- Dark mode support
- Bill text analysis with Anthropic API
- Tag system implementation

### In Development
- Enhanced bill analysis capabilities
- Additional data visualizations
- Advanced search functionality
- Multi-select tag filtering

### Upcoming Features (AWS Migration)
- User authentication with Google Sign-In
- Advanced analytics dashboard
- Enhanced security measures
- Serverless architecture deployment

## Future Enhancements

### AWS Implementation Features
1. **Analytics Dashboard**
   - Voting pattern analysis
   - Bill success rate tracking
   - Member participation metrics
   - Real-time data updates

2. **Enhanced Search**
   - Elasticsearch integration
   - Full-text bill search
   - Advanced filtering options
   - Contextual search results

3. **User Features**
   - Customizable dashboards
   - Saved searches
   - Email notifications
   - Personal bill tracking

4. **Advanced Analysis**
   - Multi-provider AI integration
   - Predictive analytics
   - Trend analysis
   - Correlation studies

### Technical Improvements
1. **Performance Optimization**
   - Query optimization
   - Caching implementation
   - Frontend performance tuning
   - Database indexing strategies

2. **Security Enhancements**
   - API authentication
   - Rate limiting
   - Data encryption
   - Security auditing

3. **Scalability**
   - Microservices architecture
   - Load balancing
   - Database sharding
   - Caching layers

## Maintenance and Operations

### Monitoring
- Error logging and tracking
- Performance monitoring
- API usage statistics
- Database health checks

### Updates
- Regular data refreshes
- API version management
- Database migrations
- Security patches

This project provides a robust foundation for legislative data analysis and visualization, with a clear path for future enhancements and scalability.
