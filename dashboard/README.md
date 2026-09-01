# Rescue Dashboard - Disaster Response System

## Overview

The **Rescue Dashboard** is a React web application for rescue personnel and emergency coordinators. It provides:

- **Real-time emergency visualization** on an interactive map
- **Priority queue management** of SOS requests
- **Damage assessment reports** from computer vision analysis
- **Team coordination tools** for rescue operations
- **Communication interface** with mobile victims and other rescue teams

## Architecture

### Core Features (Future Phases)

- **Interactive Map** - Display victim locations and emergency hotspots
- **Emergency Queue** - Prioritized list of SOS requests
- **Damage Heatmap** - Visualize structural damage from CV analysis
- **Team Dashboard** - Assign rescue teams to emergencies
- **Analytics** - Track response metrics and coverage
- **Offline Map Support** - OpenStreetMap with offline tiles

### Dashboard Sections (Phase 7+)

- Emergency Map View
- Priority Queue
- Team Management
- Analytics & Reports
- Settings
- About

## Technology Stack

- **Framework**: React 18+
- **Build Tool**: Vite
- **Language**: JavaScript
- **Styling**: Tailwind CSS
- **Maps**: Leaflet + OpenStreetMap
- **API Client**: Fetch API (or Axios)
- **State Management**: React Context/Hooks (Phase 7)

## Current Status

**Phase 1: Initialization**
- ✅ Project structure created
- ✅ Vite build system configured
- ✅ React + Tailwind CSS set up
- ✅ Directory structure for components, pages, services
- ⏳ Dashboard UI (Phase 7)
- ⏳ Map integration (Phase 7)
- ⏳ Emergency visualization (Phase 7)
- ⏳ Real-time updates (Phase 7)

## Installation

### Prerequisites

- Node.js (v18+) and npm
- Modern web browser

### Setup

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies
npm install
```

## Running the Dashboard

### Development Mode

```bash
cd dashboard
npm run dev
```

The dashboard will be available at: `http://localhost:5173/`

**Features:**
- Hot module reloading (HMR)
- Instant updates on file save
- Source maps for debugging

### Production Build

```bash
npm run build
```

Generates optimized files in `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

Runs the production build locally at `http://localhost:4173/`

## Project Structure

```
dashboard/
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── Map/        # Map components (Phase 7)
│   │   ├── Queue/      # Emergency queue components (Phase 7)
│   │   ├── Team/       # Team management (Phase 7)
│   │   └── ...
│   ├── pages/          # Full page components
│   │   ├── Dashboard.jsx       # Main page (Phase 7)
│   │   ├── Analytics.jsx       # Analytics (Phase 7)
│   │   └── ...
│   ├── services/       # API and backend services
│   │   ├── apiService.js       # Backend API calls
│   │   ├── mapService.js       # Map utilities
│   │   └── ...
│   ├── hooks/          # Custom React hooks
│   ├── utils/          # Utility functions
│   ├── assets/         # Images, icons, etc.
│   ├── App.jsx         # Root component
│   ├── main.jsx        # Entry point
│   └── index.css       # Global styles
├── index.html          # HTML template
├── vite.config.js      # Vite configuration
├── package.json        # Dependencies
├── README.md          # This file
└── .gitignore
```

## Configuration

### Tailwind CSS

Tailwind CSS is pre-configured. Add custom styles in `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Vite Configuration

Configured in `vite.config.js`:
- React plugin enabled
- Optimized bundle splitting
- Source maps for development

### Environment Variables

Create `.env` file in dashboard directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
VITE_ENVIRONMENT=development
```

Access in components:
```javascript
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

## Planned Development

### Phase 7: Dashboard UI & Visualization
- Emergency map with Leaflet
- Real-time marker updates
- Priority queue list
- Damage heatmap overlay
- Team assignment interface

### Phase 8: Integration & Deployment
- WebSocket for real-time updates
- Authentication UI
- Docker containerization
- Production optimization

## Development Guidelines

- Use functional components with hooks
- Component composition over inheritance
- Keep components under 200 lines
- Store reusable logic in hooks/
- Use Tailwind for styling consistency
- Follow React best practices

## Styling with Tailwind CSS

```jsx
// Example component
export function EmergencyCard({ emergency }) {
  return (
    <div className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition">
      <h3 className="text-lg font-bold text-red-600">{emergency.title}</h3>
      <p className="text-gray-600 mt-2">{emergency.description}</p>
      <div className="mt-4 flex gap-2">
        <button className="bg-blue-500 text-white px-4 py-2 rounded">Assign</button>
        <button className="bg-gray-300 px-4 py-2 rounded">Details</button>
      </div>
    </div>
  );
}
```

## Building & Deployment

### Local Production Build

```bash
npm run build
npm run preview
```

### Docker Deployment

Create `Dockerfile` in dashboard:

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview"]
```

Build and run:
```bash
docker build -t disaster-dashboard .
docker run -p 5173:5173 disaster-dashboard
```

## Testing

Manual testing:

```bash
# Start dev server
npm run dev

# Test in browser
# http://localhost:5173/
```

Automated testing (Phase 7+):

```bash
# Install testing dependencies
npm install -D vitest @testing-library/react

# Run tests
npm run test
```

## Performance Optimization

- Code splitting with dynamic imports
- Image lazy loading
- CSS minification in production
- Bundle analysis with `vite-plugin-visualizer`

## Troubleshooting

### Port 5173 already in use

```bash
# Kill process using port
lsof -i :5173 | grep -v COMMAND | awk '{print $2}' | xargs kill -9

# Or use different port
npm run dev -- --port 3000
```

### Module not found error

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Map not displaying

- Check API URL in environment variables
- Verify OpenStreetMap tile server is accessible
- Check browser console for errors

## Related Documentation

- [System Architecture](../docs/architecture.md)
- [API Documentation](../docs/api.md)
- [Database Schema](../docs/database.md)

## Resources

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [Leaflet Documentation](https://leafletjs.com/)
- [OpenStreetMap](https://www.openstreetmap.org/)

---

**Phase**: 1 (Initialization)  
**Status**: ✅ Ready for Phase 7 (UI Development)  
**Last Updated**: August 2026
