# TODO

## MVP Ready - Critical Tasks

### 1. Last Updated Timestamp
- [ ] Fix "Last updated: [placeholder]" in header (App.jsx line 233)
- [ ] Create API endpoint to get the most recent `last_update` date from database
- [ ] Display actual last update date in header dynamically

### 2. Data Updates & ESMA Integration
- [ ] Implement automatic data download from ESMA website
- [ ] Create script/endpoint to fetch CSV from ESMA register URL
- [ ] Update "Last updated" timestamp dynamically based on data import
- [ ] Set up scheduled data updates (cron job or similar)
- [ ] Handle CSV encoding and parsing from ESMA source

## Future Improvements

### 3. Error Handling & UX
- [ ] Add user-facing error messages for API failures
- [ ] Add "No entities found" message when filters return empty results
- [ ] Improve error handling in Filters component

### 4. Production Configuration
- [ ] Configure CORS for production domain
- [ ] Add environment variables for API URL in production
- [ ] Test production build and deployment

*Last updated: 2025-01-27*

