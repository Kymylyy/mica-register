import { useState, useEffect, useRef, useCallback } from 'react';
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
  const [filtersVisible, setFiltersVisible] = useState(true);
  const modalRef = useRef(null);
  const searchDebounceRef = useRef(null);
  const isInitialMount = useRef(true);

  const fetchEntities = useCallback(async (showLoading = true) => {
    if (showLoading) {
      setLoading(true);
    }
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
  }, [filters]);

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
      fetchEntities(true); // Show loading for search
    }, 100); // 100ms delay

    // Cleanup function
    return () => {
      if (searchDebounceRef.current) {
        clearTimeout(searchDebounceRef.current);
      }
    };
  }, [filters.search, fetchEntities]);

  // Immediate effect for other filters (non-search)
  useEffect(() => {
    // Skip on initial mount
    if (isInitialMount.current) return;

    // For other filter changes, fetch immediately (but cancel any pending search debounce)
    // Don't show loading state to avoid flickering - keep previous data visible
    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }
    fetchEntities(false); // Don't show loading state
  }, [filters.home_member_states, filters.service_codes, filters.auth_date_from, filters.auth_date_to, fetchEntities]);

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


  // Presentational component for pill-style contact links
  const ContactPill = ({ href, children, external = false, icon }) => (
    <a
      href={href}
      target={external ? "_blank" : undefined}
      rel={external ? "noopener noreferrer" : undefined}
      className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-700 transition-all hover:border-sky-300 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1"
      aria-label={typeof children === 'string' ? children : undefined}
    >
      {icon && <span className="flex-shrink-0 text-slate-500">{icon}</span>}
      <span className="text-xs">{children}</span>
    </a>
  );

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="py-4">
        {/* Header Section */}
        <header className="mb-3 max-w-7xl mx-auto px-4 lg:px-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-3 animate-fade-in">
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
              {/* Left: Title + Subtitle */}
              <div className="flex-1">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 mb-1">
                  Crypto-asset service provider register
                </h1>
                <p className="text-sm text-slate-600">
                  Last updated: [placeholder] • ESMA register{' '}
                  <a
                    href="https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica#InterimMiCARegister"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sky-600 hover:text-sky-700 hover:underline transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-1 rounded-sm font-medium"
                  >
                    available here
                  </a>
                </p>
              </div>
            
                      {/* Right: Feedback + Contact utility panel */}
                      <div className="flex flex-col items-start md:items-end gap-2 mt-[2px] lg:mt-[3px]">
                        <p className="text-xs uppercase tracking-[0.16em] text-slate-500/60 mb-1">
                          Feedback / suggest improvement
                        </p>
                        <div className="flex flex-wrap gap-2">
                          <ContactPill
                            href="mailto:k.moson@taylorwessing.com"
                            icon={
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                              </svg>
                            }
                          >
                            k.moson@taylorwessing.com
                          </ContactPill>
                          <ContactPill
                            href="https://www.linkedin.com/in/kamilmoson/"
                            external
                            icon={
                              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                              </svg>
                            }
                          >
                            LinkedIn
                          </ContactPill>
                        </div>
                      </div>
          </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-3 lg:px-6">
          <Filters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onClearFilters={handleClearFilters}
          isVisible={filtersVisible}
          onToggleVisibility={() => setFiltersVisible(!filtersVisible)}
        />

        <div className="relative">
          {loading && entities.length === 0 && (
            <div className="text-center py-12">
              <div className="text-gray-500">Loading...</div>
            </div>
          )}
          {entities.length > 0 && (
            <div className="transition-opacity duration-300 ease-in-out">
              <DataTable data={entities} onRowClick={handleRowClick} count={count} />
              {loading && (
                <div className="absolute top-0 right-0 mt-2 mr-4 z-10">
                  <div className="bg-white rounded-lg shadow-md px-3 py-2 flex items-center gap-2 text-sm text-gray-600 border border-gray-200">
                    <svg className="animate-spin h-4 w-4 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Updating...</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Entity Details Modal */}
        {selectedEntity && (
          <div 
            ref={modalRef}
            className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in"
            onClick={(e) => {
              if (e.target === modalRef.current || e.target.closest('.modal-content') === null) {
                handleCloseDetails();
              }
            }}
          >
            <div className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto modal-content shadow-2xl animate-slide-down">
              <div className="p-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8 pb-6 border-b border-gray-200">
                  <h2 className="text-3xl font-bold text-gray-900">
                    {selectedEntity.commercial_name || selectedEntity.lei_name}
                  </h2>
                  <button
                    onClick={handleCloseDetails}
                    className="text-gray-400 hover:text-gray-600 text-3xl leading-none transition-colors rounded-full hover:bg-gray-100 w-10 h-10 flex items-center justify-center"
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

                <div className="space-y-6">
                  {/* All data in single line format */}
                  <div className="space-y-5">
                    {/* LEI */}
                    <div className="flex items-center gap-4">
                      <label className="text-base font-semibold text-gray-600 w-40 flex-shrink-0 flex items-center gap-2">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                        </svg>
                        LEI
                      </label>
                      <div className="flex items-center gap-2 flex-1">
                        <p className="text-base text-gray-900 font-medium">{selectedEntity.lei || '-'}</p>
                        {selectedEntity.lei && (
                          <button
                            onClick={() => handleCopy(selectedEntity.lei, 'LEI')}
                            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded hover:bg-gray-100"
                            title="Copy LEI"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
        </button>
                        )}
                      </div>
                    </div>

                    {/* Home Member State */}
                    <div className="flex items-center gap-4">
                      <label className="text-base font-semibold text-gray-600 w-40 flex-shrink-0 flex items-center gap-2">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Home Member State
                      </label>
                      <div className="flex items-center gap-2">
                        {selectedEntity.home_member_state && getCountryFlag(selectedEntity.home_member_state) && (
                          <span>{getCountryFlag(selectedEntity.home_member_state)}</span>
                        )}
                        <p className="text-base text-gray-900 font-medium">
                          {selectedEntity.home_member_state 
                            ? (COUNTRY_NAMES[selectedEntity.home_member_state] || selectedEntity.home_member_state)
                            : '-'}
                        </p>
                      </div>
                    </div>

                    {/* Competent Authority */}
                    <div className="flex items-center gap-4">
                      <label className="text-base font-semibold text-gray-600 w-40 flex-shrink-0 flex items-center gap-2">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                        Competent Authority
                      </label>
                      <p className="text-base text-gray-900 font-medium">{selectedEntity.competent_authority || '-'}</p>
                    </div>

                    {/* Address */}
                    <div className="flex items-center gap-4">
                      <label className="text-base font-semibold text-gray-600 w-40 flex-shrink-0 flex items-center gap-2">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        Address
                      </label>
                      <div className="flex items-center gap-2 flex-1">
                        <p className="text-base text-gray-900 font-medium">{selectedEntity.address || '-'}</p>
                        {selectedEntity.address && (
                          <button
                            onClick={() => handleCopy(selectedEntity.address, 'Address')}
                            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded hover:bg-gray-100"
                            title="Copy address"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Website */}
                    <div className="flex items-center gap-4">
                      <label className="text-base font-semibold text-gray-600 w-40 flex-shrink-0 flex items-center gap-2">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                        </svg>
                        Website
                      </label>
                      <div className="flex items-center gap-2 flex-1">
                        {selectedEntity.website ? (
                          <>
                            <a
                              href={selectedEntity.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline font-medium text-base"
                            >
                              {selectedEntity.website}
                            </a>
                            <button
                              onClick={() => handleCopy(selectedEntity.website, 'Website')}
                              className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded hover:bg-gray-100"
                              title="Copy website"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                            </button>
                          </>
                        ) : (
                          <p className="text-base text-gray-900 font-medium">-</p>
                        )}
                      </div>
      </div>

                    {/* Authorisation / Notification Date */}
                    <div className="flex items-center gap-4">
                      <label className="text-base font-semibold text-gray-600 w-40 flex-shrink-0 flex items-center gap-2">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        Authorisation / Notification Date
                      </label>
                      <p className="text-base text-gray-900 font-medium">
                        {formatDate(selectedEntity.authorisation_notification_date)}
                      </p>
                    </div>

                    {/* Services */}
                    <div className="flex items-start gap-4">
                      <label className="text-base font-semibold text-gray-600 w-40 flex-shrink-0 flex items-center gap-2 pt-1">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        Services
                      </label>
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
                                    className="px-4 py-2 text-sm font-medium bg-blue-100 text-blue-800 rounded-lg border border-blue-200"
                                  >
                                    {fullDescriptionCapitalized}
                                  </span>
                                );
                              })}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-base font-medium">-</p>
                        )}
                      </div>
                    </div>

                    {/* Passport Countries */}
                    {selectedEntity.passport_countries && selectedEntity.passport_countries.length > 0 && (
                      <div className="flex items-start gap-4">
                        <label className="text-base font-semibold text-gray-600 w-40 flex-shrink-0 flex items-center gap-2 pt-1">
                          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Passport Countries
                        </label>
                        <div className="flex flex-wrap gap-2 flex-1">
                          {selectedEntity.passport_countries.map((country, idx) => (
                            <div key={idx} className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg text-sm font-medium border border-gray-200">
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
                <div className="mt-8 pt-6 border-t border-gray-200 text-sm text-gray-500 text-center">
                  Press <kbd className="px-2 py-1 bg-gray-100 rounded border border-gray-300 font-mono text-xs">ESC</kbd> to close, 
                  <kbd className="px-2 py-1 bg-gray-100 rounded border border-gray-300 font-mono text-xs mx-1">←</kbd>
                  <kbd className="px-2 py-1 bg-gray-100 rounded border border-gray-300 font-mono text-xs">→</kbd> to navigate
                </div>
              </div>
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}

export default App;
