import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { DataTable } from './components/DataTable';
import { Filters } from './components/Filters';
import { getCountryFlag } from './components/FlagIcon';
import { formatDate, copyToClipboard } from './utils/modalUtils';
import { getServiceDescription, getServiceShortName, getServiceDescriptionCapitalized, getServiceCodeOrder } from './utils/serviceDescriptions';

// Country code to full English name mapping
const COUNTRY_NAMES = {
  'AT': 'Austria',
  'BE': 'Belgium',
  'BG': 'Bulgaria',
  'CY': 'Cyprus',
  'CZ': 'Czech Republic',
  'DE': 'Germany',
  'DK': 'Denmark',
  'EE': 'Estonia',
  'ES': 'Spain',
  'FI': 'Finland',
  'FR': 'France',
  'GR': 'Greece',
  'HR': 'Croatia',
  'HU': 'Hungary',
  'IE': 'Ireland',
  'IS': 'Iceland',
  'IT': 'Italy',
  'LI': 'Liechtenstein',
  'LT': 'Lithuania',
  'LU': 'Luxembourg',
  'LV': 'Latvia',
  'MT': 'Malta',
  'NL': 'Netherlands',
  'NO': 'Norway',
  'PL': 'Poland',
  'PT': 'Portugal',
  'RO': 'Romania',
  'SE': 'Sweden',
  'SI': 'Slovenia',
  'SK': 'Slovakia',
  'EL': 'Greece',
};

function App() {
  const [entities, setEntities] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [filters, setFilters] = useState({});
  const [copyFeedback, setCopyFeedback] = useState(null);
  const modalRef = useRef(null);
  const searchDebounceRef = useRef(null);
  const isInitialMount = useRef(true);

  const fetchEntities = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.home_member_states && filters.home_member_states.length > 0) {
        filters.home_member_states.forEach(state => {
          params.append('home_member_states', state);
        });
      }
      if (filters.service_codes && filters.service_codes.length > 0) {
        filters.service_codes.forEach(code => {
          params.append('service_codes', code);
        });
      }
      if (filters.auth_date_from) params.append('auth_date_from', filters.auth_date_from);
      if (filters.auth_date_to) params.append('auth_date_to', filters.auth_date_to);

      const [entitiesRes, countRes] = await Promise.all([
        axios.get(`/api/entities?${params.toString()}&limit=1000`),
        axios.get(`/api/entities/count?${params.toString()}`),
      ]);

      setEntities(entitiesRes.data);
      setCount(countRes.data.count);
    } catch (error) {
      console.error('Error fetching entities:', error);
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch on mount
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      fetchEntities();
      return;
    }
  }, []);

  // Debounced effect for search - only triggers after user stops typing for 400ms
  useEffect(() => {
    // Skip on initial mount
    if (isInitialMount.current) return;

    // Clear previous timeout
    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }

    // Debounce search changes
    searchDebounceRef.current = setTimeout(() => {
      fetchEntities();
    }, 100); // 100ms delay

    // Cleanup function
    return () => {
      if (searchDebounceRef.current) {
        clearTimeout(searchDebounceRef.current);
      }
    };
  }, [filters.search]);

  // Immediate effect for other filters (non-search)
  useEffect(() => {
    // Skip on initial mount
    if (isInitialMount.current) return;

    // For other filter changes, fetch immediately (but cancel any pending search debounce)
    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }
    fetchEntities();
  }, [filters.home_member_states, filters.service_codes, filters.auth_date_from, filters.auth_date_to]);

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleClearFilters = () => {
    setFilters({});
  };

  const handleRowClick = (entity) => {
    setSelectedEntity(entity);
  };

  const handleCloseDetails = () => {
    setSelectedEntity(null);
  };


  // Keyboard navigation
  useEffect(() => {
    if (!selectedEntity) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        handleCloseDetails();
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        const currentIndex = entities.findIndex(e => e.id === selectedEntity.id);
        if (currentIndex === -1) return;

        let newIndex;
        if (e.key === 'ArrowLeft') {
          newIndex = currentIndex > 0 ? currentIndex - 1 : entities.length - 1;
        } else {
          newIndex = currentIndex < entities.length - 1 ? currentIndex + 1 : 0;
        }

        setSelectedEntity(entities[newIndex]);
        // Refresh entity details
        axios.get(`/api/entities/${entities[newIndex].id}`)
          .then(response => setSelectedEntity(response.data))
          .catch(error => console.error('Error fetching entity:', error));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedEntity, entities]);

  // Handle copy to clipboard
  const handleCopy = async (text, label) => {
    const success = await copyToClipboard(text);
    if (success) {
      setCopyFeedback(`${label} copied!`);
      setTimeout(() => setCopyFeedback(null), 2000);
    }
  };


  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            MiCA Register
          </h1>
          <p className="text-gray-600">
            Crypto-asset service providers register
          </p>
        </header>

        <Filters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onClearFilters={handleClearFilters}
        />

        <div className="mb-4 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Showing <span className="font-semibold">{count}</span> entities
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="text-gray-500">Loading...</div>
          </div>
        ) : (
          <DataTable data={entities} onRowClick={handleRowClick} />
        )}

        {/* Entity Details Modal */}
        {selectedEntity && (
          <div 
            ref={modalRef}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            onClick={(e) => {
              if (e.target === modalRef.current || e.target.closest('.modal-content') === null) {
                handleCloseDetails();
              }
            }}
          >
            <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto modal-content">
              <div className="p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selectedEntity.commercial_name || selectedEntity.lei_name}
                  </h2>
                  <button
                    onClick={handleCloseDetails}
                    className="text-gray-400 hover:text-gray-600 text-3xl leading-none"
                    title="Close (ESC)"
                  >
                    ×
                  </button>
                </div>

                {/* Copy feedback */}
                {copyFeedback && (
                  <div className="mb-4 p-2 bg-green-100 text-green-800 text-sm rounded text-center">
                    {copyFeedback}
                  </div>
                )}

                <div className="space-y-4">
                  {/* All data in single line format */}
                  <div className="space-y-3">
                    {/* LEI */}
                    <div className="flex items-center gap-3">
                      <label className="text-sm font-medium text-gray-500 w-32 flex-shrink-0">LEI</label>
                      <div className="flex items-center gap-2 flex-1">
                        <p className="text-gray-900">{selectedEntity.lei || '-'}</p>
                        {selectedEntity.lei && (
                          <button
                            onClick={() => handleCopy(selectedEntity.lei, 'LEI')}
                            className="text-gray-400 hover:text-gray-600"
                            title="Copy LEI"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Home Member State */}
                    <div className="flex items-center gap-3">
                      <label className="text-sm font-medium text-gray-500 w-32 flex-shrink-0">Home Member State</label>
                      <div className="flex items-center gap-2">
                        {selectedEntity.home_member_state && getCountryFlag(selectedEntity.home_member_state) && (
                          <span>{getCountryFlag(selectedEntity.home_member_state)}</span>
                        )}
                        <p className="text-gray-900">
                          {selectedEntity.home_member_state 
                            ? (COUNTRY_NAMES[selectedEntity.home_member_state] || selectedEntity.home_member_state)
                            : '-'}
                        </p>
                      </div>
                    </div>

                    {/* Competent Authority */}
                    <div className="flex items-center gap-3">
                      <label className="text-sm font-medium text-gray-500 w-32 flex-shrink-0">Competent Authority</label>
                      <p className="text-gray-900">{selectedEntity.competent_authority || '-'}</p>
                    </div>

                    {/* Address */}
                    <div className="flex items-center gap-3">
                      <label className="text-sm font-medium text-gray-500 w-32 flex-shrink-0">Address</label>
                      <div className="flex items-center gap-2 flex-1">
                        <p className="text-gray-900">{selectedEntity.address || '-'}</p>
                        {selectedEntity.address && (
                          <button
                            onClick={() => handleCopy(selectedEntity.address, 'Address')}
                            className="text-gray-400 hover:text-gray-600"
                            title="Copy address"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Website */}
                    <div className="flex items-center gap-3">
                      <label className="text-sm font-medium text-gray-500 w-32 flex-shrink-0">Website</label>
                      <div className="flex items-center gap-2 flex-1">
                        {selectedEntity.website ? (
                          <>
                            <a
                              href={selectedEntity.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline"
                            >
                              {selectedEntity.website}
                            </a>
                            <button
                              onClick={() => handleCopy(selectedEntity.website, 'Website')}
                              className="text-gray-400 hover:text-gray-600"
                              title="Copy website"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                            </button>
                          </>
                        ) : (
                          <p className="text-gray-900">-</p>
                        )}
                      </div>
                    </div>

                    {/* Authorisation / Notification Date */}
                    <div className="flex items-center gap-3">
                      <label className="text-sm font-medium text-gray-500 w-32 flex-shrink-0">Authorisation / Notification Date</label>
                      <p className="text-gray-900">
                        {formatDate(selectedEntity.authorisation_notification_date)}
                      </p>
                    </div>

                    {/* Services */}
                    <div className="flex items-start gap-3">
                      <label className="text-sm font-medium text-gray-500 w-32 flex-shrink-0 pt-1">Services</label>
                      <div className="flex-1">
                        {selectedEntity.services && selectedEntity.services.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {[...selectedEntity.services]
                              .sort((a, b) => getServiceCodeOrder(a.code) - getServiceCodeOrder(b.code))
                              .map((service, idx) => {
                                const fullDescriptionCapitalized = getServiceDescriptionCapitalized(service.code);
                                return (
                                  <span
                                    key={idx}
                                    className="px-3 py-1.5 text-xs bg-blue-100 text-blue-800 rounded-md"
                                  >
                                    {fullDescriptionCapitalized}
                                  </span>
                                );
                              })}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-sm">-</p>
                        )}
                      </div>
                    </div>

                    {/* Passport Countries */}
                    {selectedEntity.passport_countries && selectedEntity.passport_countries.length > 0 && (
                      <div className="flex items-start gap-3">
                        <label className="text-sm font-medium text-gray-500 w-32 flex-shrink-0 pt-1">Passport Countries</label>
                        <div className="flex flex-wrap gap-2 flex-1">
                          {selectedEntity.passport_countries.map((country, idx) => (
                            <div key={idx} className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-sm">
                              {getCountryFlag(country.country_code) && (
                                <span>{getCountryFlag(country.country_code)}</span>
                              )}
                              <span className="text-gray-900">{country.country_code}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Keyboard navigation hint */}
                <div className="mt-6 pt-4 border-t border-gray-200 text-xs text-gray-500 text-center">
                  Press <kbd className="px-1.5 py-0.5 bg-gray-100 rounded">ESC</kbd> to close, 
                  <kbd className="px-1.5 py-0.5 bg-gray-100 rounded mx-1">←</kbd>
                  <kbd className="px-1.5 py-0.5 bg-gray-100 rounded">→</kbd> to navigate
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
