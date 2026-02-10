import { useState, useEffect, useRef, useCallback } from 'react';
import { Analytics } from '@vercel/analytics/react';
import axios from 'axios';
import api from './utils/api';
import { DataTable } from './components/DataTable';
import { Filters } from './components/Filters';
import { RegisterSelector } from './components/RegisterSelector';
import { FlagIcon } from './components/FlagIcon';
import { ContactPill } from './components/ContactPill';
import { formatDate, copyToClipboard } from './utils/modalUtils';
import { getServiceCodeOrder, getServiceMediumName } from './utils/serviceDescriptions';
import { useDebounce } from './utils/debounce';
import { COUNTRY_NAMES } from './utils/countryNames';

const PAGE_SIZE = 100;

function formatHeaderDate(isoDate) {
  if (!isoDate) return 'N/A';

  const parts = isoDate.split('-');
  if (parts.length !== 3) return 'N/A';

  const [year, month, day] = parts.map(Number);
  if (!year || !month || !day) return 'N/A';

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];
  const monthName = monthNames[month - 1];
  if (!monthName) return 'N/A';

  return `${day} ${monthName} ${year}`;
}

function App({ registerType = 'casp' }) {
  const [entities, setEntities] = useState([]);
  const [count, setCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [filters, setFilters] = useState({});
  const [copyFeedback, setCopyFeedback] = useState(null);
  const [filtersVisible, setFiltersVisible] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const modalRef = useRef(null);
  const isInitialMount = useRef(true);
  const abortControllerRef = useRef(null);

  // Debounce search input (300ms) for better performance
  const debouncedSearch = useDebounce(filters.search, 300);

  const fetchEntities = useCallback(async (showLoading = true, searchValue = debouncedSearch) => {
    // Cancel any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new AbortController for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    if (showLoading) {
      setLoading(true);
    }
    try {
      const params = new URLSearchParams();

      // Add register type
      params.append('register_type', registerType);
      params.append('limit', String(PAGE_SIZE));
      params.append('skip', String((currentPage - 1) * PAGE_SIZE));

      // Use debounced search value instead of direct filters.search
      if (searchValue) params.append('search', searchValue);
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

      const entitiesRes = await api.get(`/api/entities?${params.toString()}`, {
        signal: abortController.signal
      });

      // Only update state if this request wasn't cancelled
      if (!abortController.signal.aborted) {
        // API now returns paginated response with items array
        setEntities(entitiesRes.data.items || []);
        setCount(entitiesRes.data.total !== undefined ? entitiesRes.data.total : 0);
      }
    } catch (error) {
      // Ignore errors from cancelled requests
      if (
        error.name === 'CanceledError' ||
        error.name === 'AbortError' ||
        error.code === 'ERR_CANCELED' ||
        error.message === 'canceled' ||
        axios.isCancel(error) ||
        abortController.signal.aborted
      ) {
        return;
      }
      console.error('Error fetching entities:', error);
    } finally {
      // Only update loading state if this request wasn't cancelled
      if (!abortController.signal.aborted) {
        setLoading(false);
      }
    }
  }, [filters, debouncedSearch, registerType, currentPage]);

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Initial fetch on mount
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      fetchEntities();
      return;
    }
  }, []);

  // Effect for register type change - reset filters
  useEffect(() => {
    // Skip on initial mount
    if (isInitialMount.current) return;

    // Reset filters when register type changes
    // The filters effect below will handle fetching with new registerType
    setFilters({});
    setCurrentPage(1);
    setSelectedEntity(null);
  }, [registerType]);

  // Effect for all filters - uses debounced search for better performance
  // Also triggers on registerType change (via fetchEntities dependency)
  useEffect(() => {
    // Skip on initial mount
    if (isInitialMount.current) return;

    // Fetch with debounced search - AbortController will cancel any previous request
    // Show loading for better UX
    fetchEntities(true);
  }, [debouncedSearch, filters.home_member_states, filters.service_codes, filters.auth_date_from, filters.auth_date_to, fetchEntities, currentPage]);

  useEffect(() => {
    let cancelled = false;

    const fetchLastUpdated = async () => {
      try {
        const response = await api.get('/api/metadata/last-updated', {
          params: { register_type: registerType },
        });
        if (!cancelled) {
          setLastUpdated(response.data?.last_updated || null);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Error fetching last updated metadata:', error);
          setLastUpdated(null);
        }
      }
    };

    fetchLastUpdated();
    return () => {
      cancelled = true;
    };
  }, [registerType]);

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  const handleClearFilters = () => {
    setFilters({});
    setCurrentPage(1);
  };

  const handleRowClick = (entity) => {
    setSelectedEntity(entity);
  };

  const handleCloseDetails = () => {
    setSelectedEntity(null);
  };

  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE));
  const startItem = count === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1;
  const endItem = count === 0 ? 0 : Math.min((currentPage - 1) * PAGE_SIZE + entities.length, count);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);


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
        api.get(`/api/entities/${entities[newIndex].id}`)
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
    <div className="min-h-screen flex flex-col bg-gray-100">
      <div className="py-4">
        {/* Header Section */}
        <header className="mb-3 max-w-7xl mx-auto px-4 lg:px-6">
          <div className="bg-white rounded-lg shadow-[0_1px_2px_rgba(0,0,0,0.04)] border border-gray-200 p-4 mb-3 animate-fade-in">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
              {/* Left: Title + Subtitle */}
              <div className="flex-1">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 mb-1">
                  MiCA Registers
                </h1>
                <p className="text-sm text-slate-600">
                  ESMA registers{' '}
                  <a
                    href="https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica#InterimMiCARegister"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sky-600 hover:text-sky-700 hover:underline transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-1 rounded-sm font-medium"
                  >
                    available here
                  </a>
                  {' '}• Last updated: {formatHeaderDate(lastUpdated)}
                </p>
              </div>

              {/* Right: Contact Pills */}
              <div className="flex items-center gap-2">
                <ContactPill
                  href="mailto:kamil.marek.moson@gmail.com"
                  icon={
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  }
                  text="kamil.marek.moson@gmail.com"
                />
                <ContactPill
                  href="https://www.linkedin.com/in/kamilmoson/"
                  icon={
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                  }
                  text="Kamil Mosoń"
                />
              </div>
          </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-3 lg:px-6">
          {/* Register type selector tabs */}
          <RegisterSelector />

          {/* Show filters if there are results OR if any filters are active (so user can clear them) */}
          {(() => {
            const hasActiveFilters = !!(
              filters.search ||
              (filters.home_member_states && filters.home_member_states.length > 0) ||
              (filters.service_codes && filters.service_codes.length > 0) ||
              filters.auth_date_from ||
              filters.auth_date_to
            );
            return (!loading || count > 0 || hasActiveFilters) && (count > 0 || hasActiveFilters);
          })() && (
            <Filters
              registerType={registerType}
              filters={filters}
              onFiltersChange={handleFiltersChange}
              onClearFilters={handleClearFilters}
              isVisible={filtersVisible}
              onToggleVisibility={() => setFiltersVisible(!filtersVisible)}
            />
          )}

        <div className="h-px bg-slate-100 my-4" />

        <div className="relative">
          {loading && entities.length === 0 && (
            <div className="text-center py-12">
              <div className="text-gray-500">Loading...</div>
            </div>
          )}
          {!loading && entities.length === 0 && (
            <div className="text-center py-12">
              <div className="text-gray-500">
                {registerType === 'art'
                  ? 'No ART entered into register'
                  : 'No results found'}
              </div>
            </div>
          )}
          {entities.length > 0 && (
            <div className="transition-opacity duration-300 ease-in-out">
              <DataTable data={entities} onRowClick={handleRowClick} count={count} registerType={registerType} />
              <div className="mt-4 mb-2 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div className="text-sm text-gray-600">
                  Showing {startItem}-{endItem} of {count}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setCurrentPage(prev => Math.max(1, prev - 1));
                      setSelectedEntity(null);
                    }}
                    disabled={loading || currentPage <= 1}
                    className="px-3 py-1.5 text-sm rounded-md border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-gray-700 min-w-[90px] text-center">
                    Page {currentPage} / {totalPages}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setCurrentPage(prev => Math.min(totalPages, prev + 1));
                      setSelectedEntity(null);
                    }}
                    disabled={loading || currentPage >= totalPages}
                    className="px-3 py-1.5 text-sm rounded-md border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
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
          <>
            {/* Overlay backdrop */}
            <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 animate-fade-in" />
            
            {/* Modal panel wrapper */}
            <div 
              ref={modalRef}
              className="fixed inset-0 z-50 flex items-center justify-center"
              onClick={(e) => {
                if (e.target === modalRef.current || e.target.closest('.modal-content') === null) {
                  handleCloseDetails();
                }
              }}
            >
              <div className="bg-white shadow-xl rounded-2xl max-w-3xl w-full max-h-[80vh] overflow-y-auto modal-content animate-slide-down mx-4">
                <div className="p-6 md:p-8">
                {/* Header with overview */}
                <div className="flex items-start justify-between mb-6">
                  <div className="flex-1">
                    <h2 className="text-xl font-semibold text-textMain mb-2">
                      {selectedEntity.commercial_name || selectedEntity.lei_name}
                    </h2>
                    {/* Overview line */}
                    <div className="text-[clamp(0.7rem,1.5vw,0.875rem)] text-textMuted flex items-center gap-2 whitespace-nowrap overflow-hidden">
                      {selectedEntity.home_member_state && (
                        <FlagIcon countryCode={selectedEntity.home_member_state} size="sm" />
                      )}
                      {selectedEntity.home_member_state && (
                        <span>{COUNTRY_NAMES[selectedEntity.home_member_state] || selectedEntity.home_member_state}</span>
                      )}
                      {selectedEntity.competent_authority && (
                        <>
                          <span>•</span>
                          <span>{selectedEntity.competent_authority}</span>
                        </>
                      )}
                      {selectedEntity.authorisation_notification_date && (
                        <>
                          <span>•</span>
                          <span>Authorised: {formatDate(selectedEntity.authorisation_notification_date)}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={handleCloseDetails}
                    className="text-textSoft hover:text-textMain transition-colors p-1.5 rounded-full hover:bg-surfaceAlt ml-4"
                    title="Close (ESC)"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Copy feedback */}
                {copyFeedback && (
                  <div className="mb-4 p-2 bg-green-100 text-green-800 text-sm rounded text-center">
                    {copyFeedback}
      </div>
                )}

                {/* Two-column main section */}
                <div className="mt-4 grid gap-8 md:grid-cols-2">
                  {/* Left column: Entity details */}
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <svg className="h-4 w-4 text-textSoft" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <h3 className="text-[11px] font-semibold uppercase tracking-wide text-textSoft">
                        Entity details
                      </h3>
                    </div>
                    <dl className="space-y-3">
                      {/* LEI */}
                      <div>
                        <dt className="text-xs font-medium text-textSoft mb-0.5">LEI</dt>
                        <dd className="flex items-center gap-2 text-sm text-textMain">
                          <span>{selectedEntity.lei || '-'}</span>
                          {selectedEntity.lei && (
                            <button
                              onClick={() => handleCopy(selectedEntity.lei, 'LEI')}
                              className="text-textSoft hover:text-textMain transition-colors p-1 rounded hover:bg-surfaceAlt"
                              title="Copy LEI"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                            </button>
                          )}
                        </dd>
                      </div>

                      {/* LEI Name (Legal Name) */}
                      <div>
                        <dt className="text-xs font-medium text-textSoft mb-0.5">LEI Name (Legal Name)</dt>
                        <dd className="flex items-center gap-2 text-sm text-textMain">
                          <span>{selectedEntity.lei_name || '-'}</span>
                          {selectedEntity.lei_name && (
                            <button
                              onClick={() => handleCopy(selectedEntity.lei_name, 'LEI Name')}
                              className="text-textSoft hover:text-textMain transition-colors p-1 rounded hover:bg-surfaceAlt"
                              title="Copy LEI Name"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                            </button>
                          )}
                        </dd>
                      </div>

                      {/* Address */}
                      <div>
                        <dt className="text-xs font-medium text-textSoft mb-0.5">Address</dt>
                        <dd className="text-sm text-textMain leading-snug text-justify">
                          {selectedEntity.address ? (
                            <>
                              {selectedEntity.address}
                              <button
                                onClick={() => handleCopy(selectedEntity.address, 'Address')}
                                className="ml-2 text-textSoft hover:text-textMain transition-colors p-1 rounded hover:bg-surfaceAlt inline-flex items-center"
                                title="Copy address"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                              </button>
                            </>
                          ) : (
                            '-'
                          )}
                        </dd>
                      </div>

                      {/* Website */}
                      <div>
                        <dt className="text-xs font-medium text-textSoft mb-0.5">Website</dt>
                        <dd className="flex flex-wrap items-center gap-2 text-sm text-textMain">
                          {selectedEntity.website ? (
                            (() => {
                              // Split website by space to handle multiple URLs
                              const websites = selectedEntity.website.split(/\s+/).filter(w => w.trim());
                              return websites.length > 0 ? (
                                <>
                                  {websites.map((website, index) => {
                                    const url = website.startsWith('http://') || website.startsWith('https://') 
                                      ? website 
                                      : `https://${website}`;
                                    return (
                                      <span key={index} className="flex items-center gap-1">
                                        <a
                                          href={url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="text-accent hover:underline font-medium"
                                        >
                                          {website}
                                        </a>
                                        <button
                                          onClick={() => handleCopy(website, 'Website')}
                                          className="text-textSoft hover:text-textMain transition-colors p-1 rounded hover:bg-surfaceAlt"
                                          title={`Copy ${website}`}
                                        >
                                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                          </svg>
                                        </button>
                                        {index < websites.length - 1 && <span className="text-textSoft mx-1">|</span>}
                                      </span>
                                    );
                                  })}
                                </>
                              ) : '-';
                            })()
                          ) : (
                            '-'
                          )}
                        </dd>
                      </div>
                    </dl>
                  </div>

                  {/* Right column: Register-specific details */}
                  <div>
                    {/* CASP: Services */}
                    {registerType === 'casp' && (
                      <>
                        <div className="flex items-center gap-2 mb-3">
                          <svg className="h-4 w-4 text-textSoft" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                          </svg>
                          <h3 className="text-[11px] font-semibold uppercase tracking-wide text-textSoft">
                            Services
                          </h3>
                        </div>
                        {selectedEntity.services && selectedEntity.services.length > 0 ? (
                          <div className="space-y-2 text-sm text-textMain">
                            {[...selectedEntity.services]
                              .sort((a, b) => getServiceCodeOrder(a.code) - getServiceCodeOrder(b.code))
                              .map((service, idx) => {
                                const mediumName = getServiceMediumName(service.code);
                                return (
                                  <div key={idx} className="pb-2 border-b border-borderSubtle last:border-0 last:pb-0">
                                    {mediumName}
                                  </div>
                                );
                              })}
                          </div>
                        ) : (
                          <p className="text-textMuted text-sm font-medium">-</p>
                        )}
                      </>
                    )}

                    {/* OTHER: White Paper & Linked CASP */}
                    {registerType === 'other' && (
                      <dl className="space-y-3">
                        {/* White Paper URL */}
                        <div>
                          <dt className="text-xs font-medium text-textSoft mb-0.5">White Paper</dt>
                          <dd className="text-sm text-textMain">
                            {selectedEntity.white_paper_url ? (
                              <a
                                href={selectedEntity.white_paper_url.startsWith('http') ? selectedEntity.white_paper_url : `https://${selectedEntity.white_paper_url}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline break-words"
                              >
                                {selectedEntity.white_paper_url}
                              </a>
                            ) : '-'}
                          </dd>
                        </div>

                        {/* Linked CASP */}
                        {(selectedEntity.lei_casp || selectedEntity.lei_name_casp) && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">Linked CASP</dt>
                            <dd className="text-sm text-textMain">
                              {selectedEntity.lei_name_casp && (
                                <div className="font-medium">{selectedEntity.lei_name_casp}</div>
                              )}
                              {selectedEntity.lei_casp && (
                                <div className="text-xs text-gray-500">{selectedEntity.lei_casp}</div>
                              )}
                            </dd>
                          </div>
                        )}

                        {/* Offer Countries */}
                        {selectedEntity.offer_countries && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">Offer Countries</dt>
                            <dd className="text-sm text-textMain">
                              <div className="flex flex-wrap gap-1">
                                {selectedEntity.offer_countries.split('|').map((code, idx) => (
                                  <span key={idx} className="inline-flex items-center gap-1 rounded-md bg-surfaceAlt border border-borderSubtle px-2 py-[2px] text-xs text-textMuted">
                                    <FlagIcon countryCode={code.trim()} size="xs" />
                                    <span>{code.trim()}</span>
                                  </span>
                                ))}
                              </div>
                            </dd>
                          </div>
                        )}

                        {/* DTI Codes */}
                        {selectedEntity.dti_codes && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">DTI Codes</dt>
                            <dd className="text-sm text-textMain">{selectedEntity.dti_codes}</dd>
                          </div>
                        )}

                        {/* DTI FFG */}
                        {selectedEntity.dti_ffg && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">DTI FFG</dt>
                            <dd className="text-sm text-textMain">{selectedEntity.dti_ffg}</dd>
                          </div>
                        )}

                        {/* White Paper Comments */}
                        {selectedEntity.white_paper_comments && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">White Paper Comments</dt>
                            <dd className="text-sm text-textMain whitespace-pre-wrap">{selectedEntity.white_paper_comments}</dd>
                          </div>
                        )}
                      </dl>
                    )}

                    {/* ART: Asset-Referenced Tokens */}
                    {registerType === 'art' && (
                      <dl className="space-y-3">
                        {/* Credit Institution */}
                        <div>
                          <dt className="text-xs font-medium text-textSoft mb-0.5">Credit Institution</dt>
                          <dd className="text-sm text-textMain">
                            {selectedEntity.credit_institution !== null && selectedEntity.credit_institution !== undefined
                              ? (selectedEntity.credit_institution ? 'Yes' : 'No')
                              : '-'}
                          </dd>
                        </div>

                        {/* White Paper URL */}
                        {selectedEntity.white_paper_url && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">White Paper</dt>
                            <dd className="text-sm text-textMain">
                              <a
                                href={selectedEntity.white_paper_url.startsWith('http') ? selectedEntity.white_paper_url : `https://${selectedEntity.white_paper_url}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline break-words"
                              >
                                {selectedEntity.white_paper_url}
                              </a>
                            </dd>
                          </div>
                        )}

                        {/* White Paper Offer Countries */}
                        {selectedEntity.white_paper_offer_countries && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">WP Offer Countries</dt>
                            <dd className="text-sm text-textMain">
                              <div className="flex flex-wrap gap-1">
                                {selectedEntity.white_paper_offer_countries.split('|').map((code, idx) => (
                                  <span key={idx} className="inline-flex items-center gap-1 rounded-md bg-surfaceAlt border border-borderSubtle px-2 py-[2px] text-xs text-textMuted">
                                    <FlagIcon countryCode={code.trim()} size="xs" />
                                    <span>{code.trim()}</span>
                                  </span>
                                ))}
                              </div>
                            </dd>
                          </div>
                        )}

                        {/* White Paper Comments */}
                        {selectedEntity.white_paper_comments && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">White Paper Comments</dt>
                            <dd className="text-sm text-textMain whitespace-pre-wrap">{selectedEntity.white_paper_comments}</dd>
                          </div>
                        )}
                      </dl>
                    )}

                    {/* EMT: E-Money Tokens */}
                    {registerType === 'emt' && (
                      <dl className="space-y-3">
                        {/* Exemptions */}
                        <div>
                          <dt className="text-xs font-medium text-textSoft mb-0.5">Exemption 48.4</dt>
                          <dd className="text-sm text-textMain">
                            {selectedEntity.exemption_48_4 !== null && selectedEntity.exemption_48_4 !== undefined
                              ? (selectedEntity.exemption_48_4 ? 'Yes' : 'No')
                              : '-'}
                          </dd>
                        </div>

                        <div>
                          <dt className="text-xs font-medium text-textSoft mb-0.5">Exemption 48.5</dt>
                          <dd className="text-sm text-textMain">
                            {selectedEntity.exemption_48_5 !== null && selectedEntity.exemption_48_5 !== undefined
                              ? (selectedEntity.exemption_48_5 ? 'Yes' : 'No')
                              : '-'}
                          </dd>
                        </div>

                        {/* Institution Type */}
                        <div>
                          <dt className="text-xs font-medium text-textSoft mb-0.5">Institution Type</dt>
                          <dd className="text-sm text-textMain">{selectedEntity.authorisation_other_emt || '-'}</dd>
                        </div>

                        {/* White Paper URL */}
                        {selectedEntity.white_paper_url && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">White Paper</dt>
                            <dd className="text-sm text-textMain">
                              <a
                                href={selectedEntity.white_paper_url.startsWith('http') ? selectedEntity.white_paper_url : `https://${selectedEntity.white_paper_url}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline break-words"
                              >
                                {selectedEntity.white_paper_url}
                              </a>
                            </dd>
                          </div>
                        )}

                        {/* DTI Codes */}
                        {selectedEntity.dti_codes && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">DTI Codes</dt>
                            <dd className="text-sm text-textMain">{selectedEntity.dti_codes}</dd>
                          </div>
                        )}

                        {/* DTI FFG */}
                        {selectedEntity.dti_ffg && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">DTI FFG</dt>
                            <dd className="text-sm text-textMain">{selectedEntity.dti_ffg}</dd>
                          </div>
                        )}

                        {/* White Paper Comments */}
                        {selectedEntity.white_paper_comments && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">White Paper Comments</dt>
                            <dd className="text-sm text-textMain whitespace-pre-wrap">{selectedEntity.white_paper_comments}</dd>
                          </div>
                        )}
                      </dl>
                    )}

                    {/* NCASP: Non-Compliant Entities */}
                    {registerType === 'ncasp' && (
                      <dl className="space-y-3">
                        {/* Multiple Websites */}
                        {selectedEntity.websites && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">Websites</dt>
                            <dd className="text-sm text-textMain">
                              <div className="flex flex-col gap-1">
                                {selectedEntity.websites.split('|').map((url, idx) => (
                                  <a
                                    key={idx}
                                    href={url.trim().startsWith('http') ? url.trim() : `https://${url.trim()}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-primary hover:underline break-words"
                                  >
                                    {url.trim()}
                                  </a>
                                ))}
                              </div>
                            </dd>
                          </div>
                        )}

                        {/* Infringement */}
                        <div>
                          <dt className="text-xs font-medium text-textSoft mb-0.5">Infringement</dt>
                          <dd className="text-sm text-textMain">{selectedEntity.infringement || '-'}</dd>
                        </div>

                        {/* Reason */}
                        {selectedEntity.reason && selectedEntity.reason !== 'None' && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">Reason</dt>
                            <dd className="text-sm text-textMain whitespace-pre-wrap">{selectedEntity.reason}</dd>
                          </div>
                        )}

                        {/* Decision Date */}
                        {selectedEntity.decision_date && (
                          <div>
                            <dt className="text-xs font-medium text-textSoft mb-0.5">Decision Date</dt>
                            <dd className="text-sm text-textMain">{formatDate(selectedEntity.decision_date)}</dd>
                          </div>
                        )}
                      </dl>
                    )}
                  </div>
                </div>

                {/* Passport Countries - separate block at bottom (CASP only) */}
                {registerType === 'casp' && selectedEntity.passport_countries && selectedEntity.passport_countries.length > 0 && (
                  <div className="mt-6">
                    <div className="h-px bg-borderSubtle mb-4" />
                    <div className="flex items-center gap-2 mb-2">
                      <svg className="h-4 w-4 text-textSoft" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-[11px] font-semibold uppercase tracking-wide text-textSoft">
                        Passport countries
                      </span>
                    </div>
                    <div className="grid gap-2 grid-cols-4 sm:grid-cols-6 lg:grid-cols-8">
                      {selectedEntity.passport_countries.map((country, idx) => (
                        <span key={idx} className="inline-flex items-center gap-1 rounded-md bg-surfaceAlt border border-borderSubtle px-2 py-[2px] text-xs text-textMuted">
                          <FlagIcon countryCode={country.country_code} size="xs" />
                          <span>{country.country_code}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Comments - separate block */}
                {selectedEntity.comments && (
                  <div className="mt-6">
                    <div className="h-px bg-borderSubtle mb-4" />
                    <div className="flex items-center gap-2 mb-2">
                      <svg className="h-4 w-4 text-textSoft" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      <span className="text-[11px] font-semibold uppercase tracking-wide text-textSoft">
                        Comments
                      </span>
                    </div>
                    <div className="text-sm text-textMain leading-relaxed whitespace-pre-wrap text-justify">
                      {selectedEntity.comments}
                    </div>
                  </div>
                )}

                {/* Last Update - separate block */}
                {selectedEntity.last_update && (
                  <div className="mt-6">
                    <div className="h-px bg-borderSubtle mb-4" />
                    <div className="flex items-center gap-2 mb-2">
                      <svg className="h-4 w-4 text-textSoft" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-[11px] font-semibold uppercase tracking-wide text-textSoft">
                        Last Update
                      </span>
                    </div>
                    <div className="text-sm text-textMain">
                      {formatDate(selectedEntity.last_update)}
                    </div>
                  </div>
                )}

                {/* Keyboard navigation hint */}
                <div className="mt-6 text-center text-[13px] text-textSoft">
                  Press <kbd className="inline-flex items-center rounded border border-borderSubtle px-1.5 py-[1px] text-[11px] text-textSoft font-mono">ESC</kbd> to close, 
                  <kbd className="inline-flex items-center rounded border border-borderSubtle px-1.5 py-[1px] text-[11px] text-textSoft font-mono mx-1">←</kbd>
                  <kbd className="inline-flex items-center rounded border border-borderSubtle px-1.5 py-[1px] text-[11px] text-textSoft font-mono">→</kbd> to navigate
                </div>
                </div>
              </div>
            </div>
          </>
        )}
        </div>
      </div>
      <Analytics />
    </div>
  );
}

export default App;
