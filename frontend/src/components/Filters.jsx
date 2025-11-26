import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { getCountryFlag } from './FlagIcon';
import { getServiceDescriptionCapitalized, getServiceCodeOrder } from '../utils/serviceDescriptions';

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
  'EL': 'Greece', // Alternative code for Greece
};

export function Filters({ filters, onFiltersChange, onClearFilters }) {
  const [filterOptions, setFilterOptions] = useState({
    home_member_states: [],
    service_codes: [],
  });
  const [filterCounts, setFilterCounts] = useState({
    country_counts: {},
    service_counts: {},
  });
  const homeMemberStateSearchRef = useRef(null);
  const cryptoServicesSearchRef = useRef(null);
  const homeMemberStateDetailsRef = useRef(null);
  const cryptoServicesDetailsRef = useRef(null);
  const authDateDetailsRef = useRef(null);
  const authDateFromDateInputRef = useRef(null);
  const authDateToDateInputRef = useRef(null);
  const [homeMemberStateSearch, setHomeMemberStateSearch] = useState('');
  const [cryptoServicesSearch, setCryptoServicesSearch] = useState('');
  const [authDateFromInput, setAuthDateFromInput] = useState('');
  const [authDateToInput, setAuthDateToInput] = useState('');

  // Convert YYYY-MM-DD to DD-MM-YYYY for display
  const formatDateForDisplay = (dateStr) => {
    if (!dateStr) return '';
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
      const [year, month, day] = dateStr.split('-');
      return `${day}-${month}-${year}`;
    }
    return dateStr;
  };

  // Convert DD-MM-YYYY to YYYY-MM-DD for storage
  const parseDateFromInput = (input) => {
    if (!input) return null;
    const trimmed = input.trim();
    
    // If only 4 digits, treat as year
    if (/^\d{4}$/.test(trimmed)) {
      return `${trimmed}-01-01`;
    }
    
    // If DD-MM-YYYY format
    if (/^\d{2}-\d{2}-\d{4}$/.test(trimmed)) {
      const [day, month, year] = trimmed.split('-');
      return `${year}-${month}-${day}`;
    }
    
    // If YYYY-MM-DD format (already correct)
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
      return trimmed;
    }
    
    // If YYYY-MM format
    if (/^\d{4}-\d{2}$/.test(trimmed)) {
      return `${trimmed}-01`;
    }
    
    return trimmed;
  };

  useEffect(() => {
    // Fetch filter options
    axios.get('/api/filters/options')
      .then(response => {
        console.log('Filter options received:', response.data);
        console.log('Service codes:', response.data.service_codes);
        console.log('Service codes length:', response.data.service_codes?.length);
        setFilterOptions(response.data || { home_member_states: [], service_codes: [] });
      })
      .catch(error => {
        console.error('Error fetching filter options:', error);
        console.error('Error details:', error.response?.data);
      });
  }, []);

  // Sync date inputs with filters (convert YYYY-MM-DD to DD-MM-YYYY for display)
  useEffect(() => {
    if (filters.auth_date_from === null || filters.auth_date_from === undefined) {
      setAuthDateFromInput('');
    } else {
      const displayValue = formatDateForDisplay(filters.auth_date_from);
      setAuthDateFromInput(displayValue);
    }
    if (filters.auth_date_to === null || filters.auth_date_to === undefined) {
      setAuthDateToInput('');
    } else {
      const displayValue = formatDateForDisplay(filters.auth_date_to);
      setAuthDateToInput(displayValue);
    }
  }, [filters.auth_date_from, filters.auth_date_to]);

  // Fetch counts whenever filters change
  useEffect(() => {
    const params = new URLSearchParams();
    
    // Build params for country counts: include service_codes but NOT home_member_states
    if (filters.search) params.append('search', filters.search);
    if (filters.auth_date_from) params.append('auth_date_from', filters.auth_date_from);
    if (filters.auth_date_to) params.append('auth_date_to', filters.auth_date_to);
    
    // Include service_codes for country counts (but backend will ignore home_member_states)
    if (filters.service_codes && filters.service_codes.length > 0) {
      filters.service_codes.forEach(code => {
        params.append('service_codes', code);
      });
    }
    
    // Fetch country counts (backend ignores home_member_states for country_counts)
    axios.get(`/api/filters/counts?${params.toString()}`)
      .then(response => {
        setFilterCounts(prev => ({
          ...prev,
          country_counts: response.data?.country_counts || {},
        }));
      })
      .catch(error => {
        console.error('Error fetching country counts:', error);
      });
  }, [filters.search, filters.service_codes, filters.auth_date_from, filters.auth_date_to]);

  // Fetch service counts separately (with home_member_states but without service_codes)
  useEffect(() => {
    const params = new URLSearchParams();
    
    if (filters.search) params.append('search', filters.search);
    if (filters.auth_date_from) params.append('auth_date_from', filters.auth_date_from);
    if (filters.auth_date_to) params.append('auth_date_to', filters.auth_date_to);
    
    // Include home_member_states for service counts (but backend will ignore service_codes)
    if (filters.home_member_states && filters.home_member_states.length > 0) {
      filters.home_member_states.forEach(state => {
        params.append('home_member_states', state);
      });
    }
    
    // Fetch service counts (backend ignores service_codes for service_counts)
    axios.get(`/api/filters/counts?${params.toString()}`)
      .then(response => {
        setFilterCounts(prev => ({
          ...prev,
          service_counts: response.data?.service_counts || {},
        }));
      })
      .catch(error => {
        console.error('Error fetching service counts:', error);
      });
  }, [filters.search, filters.home_member_states, filters.auth_date_from, filters.auth_date_to]);

  const handleChange = (key, value) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const handleServiceCodeToggle = (code) => {
    const currentCodes = filters.service_codes || [];
    const newCodes = currentCodes.includes(code)
      ? currentCodes.filter(c => c !== code)
      : [...currentCodes, code];
    handleChange('service_codes', newCodes);
  };

  const handleHomeMemberStateToggle = (countryCode) => {
    const currentStates = filters.home_member_states || [];
    const newStates = currentStates.includes(countryCode)
      ? currentStates.filter(c => c !== countryCode)
      : [...currentStates, countryCode];
    handleChange('home_member_states', newStates);
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-4">
      <div className="flex items-center justify-end mb-4">
        <button
          onClick={onClearFilters}
          className="text-sm text-primary hover:underline"
        >
          Clear all
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Search */}
        <div>
          <input
            type="text"
            value={filters.search || ''}
            onChange={(e) => handleChange('search', e.target.value)}
            placeholder="Search by anything..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* Authorisation Date - Collapsible */}
        <div className="md:col-span-2">
          <details 
            ref={authDateDetailsRef}
            className="border border-gray-300 rounded-md"
            onToggle={(e) => {
              if (e.target.open) {
                // Auto-focus on first date input when opened
                setTimeout(() => {
                  const firstDateInput = e.target.querySelector('input[type="date"]');
                  if (firstDateInput) firstDateInput.focus();
                }, 10);
              }
            }}
            onKeyDown={(e) => {
              if (e.key === 'Escape' && authDateDetailsRef.current?.open) {
                e.preventDefault();
                authDateDetailsRef.current.open = false;
              }
            }}
          >
            <summary className="px-4 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 font-medium text-gray-700 list-none">
              <div className="flex items-center justify-between">
                <span>Authorisation / notification date</span>
                <span className="text-sm font-normal text-gray-500">
                  {filters.auth_date_from || filters.auth_date_to
                    ? `${filters.auth_date_from || '...'} - ${filters.auth_date_to || '...'}`
                    : 'Click to select'}
                </span>
              </div>
            </summary>
            <div className="p-3 bg-white border-t border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Date From */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    From
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={authDateFromInput}
                      onChange={(e) => setAuthDateFromInput(e.target.value)}
                      onBlur={() => {
                        // When user leaves the field, try to parse and format the date
                        const value = authDateFromInput.trim();
                        if (!value) {
                          handleChange('auth_date_from', null);
                          return;
                        }
                        
                        const parsed = parseDateFromInput(value);
                        if (parsed) {
                          const displayValue = formatDateForDisplay(parsed);
                          setAuthDateFromInput(displayValue);
                          handleChange('auth_date_from', parsed);
                        } else {
                          handleChange('auth_date_from', null);
                        }
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Escape' && authDateDetailsRef.current) {
                          e.preventDefault();
                          authDateDetailsRef.current.open = false;
                        } else if (e.key === 'Enter') {
                          e.preventDefault();
                          const value = authDateFromInput.trim();
                          
                          if (!value) {
                            handleChange('auth_date_from', null);
                            return;
                          }
                          
                          const parsed = parseDateFromInput(value);
                          if (parsed) {
                            const displayValue = formatDateForDisplay(parsed);
                            setAuthDateFromInput(displayValue);
                            handleChange('auth_date_from', parsed);
                          }
                          
                          // Move focus to "To" field
                          const toInput = authDateDetailsRef.current?.querySelector('input[type="text"][name="auth_date_to"]');
                          if (toInput) {
                            setTimeout(() => toInput.focus(), 10);
                          }
                        }
                      }}
                      placeholder="DD-MM-YYYY"
                      className="w-full px-3 py-2 pr-10 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                    <input
                      ref={authDateFromDateInputRef}
                      type="date"
                      value={filters.auth_date_from || ''}
                      onChange={(e) => {
                        const value = e.target.value || null;
                        if (value) {
                          const displayValue = formatDateForDisplay(value);
                          setAuthDateFromInput(displayValue);
                        } else {
                          setAuthDateFromInput('');
                        }
                        handleChange('auth_date_from', value);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Escape' && authDateDetailsRef.current) {
                          e.preventDefault();
                          authDateDetailsRef.current.open = false;
                        } else if (e.key === 'Enter') {
                          e.preventDefault();
                          // Move focus to "To" field
                          const toInput = authDateDetailsRef.current?.querySelector('input[type="text"][name="auth_date_to"]');
                          if (toInput) {
                            setTimeout(() => toInput.focus(), 10);
                          }
                        }
                      }}
                      className="absolute right-0 top-0 h-full w-10 opacity-0 pointer-events-none"
                      title="Use calendar picker"
                    />
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        if (authDateFromDateInputRef.current) {
                          authDateFromDateInputRef.current.showPicker?.();
                        }
                      }}
                      className="absolute right-0 top-0 h-full px-3 flex items-center justify-center text-gray-400 hover:text-gray-600 z-10"
                      title="Open calendar"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </div>
                </div>
                
                {/* Date To */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    To
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      name="auth_date_to"
                      value={authDateToInput}
                      onChange={(e) => setAuthDateToInput(e.target.value)}
                      onBlur={() => {
                        // When user leaves the field, try to parse and format the date
                        const value = authDateToInput.trim();
                        if (!value) {
                          handleChange('auth_date_to', null);
                          return;
                        }
                        
                        // Parse the input
                        let parsed = parseDateFromInput(value);
                        
                        // If only year (YYYY), fill with 12-31
                        if (/^\d{4}$/.test(value)) {
                          parsed = `${value}-12-31`;
                        }
                        // If YYYY-MM, fill with last day of month
                        else if (/^\d{4}-\d{2}$/.test(value)) {
                          const [year, month] = value.split('-');
                          const lastDay = new Date(parseInt(year), parseInt(month), 0).getDate();
                          parsed = `${value}-${String(lastDay).padStart(2, '0')}`;
                        }
                        
                        if (parsed) {
                          const displayValue = formatDateForDisplay(parsed);
                          setAuthDateToInput(displayValue);
                          handleChange('auth_date_to', parsed);
                        } else {
                          handleChange('auth_date_to', null);
                        }
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Escape' && authDateDetailsRef.current) {
                          e.preventDefault();
                          authDateDetailsRef.current.open = false;
                        } else if (e.key === 'Enter') {
                          e.preventDefault();
                          const value = authDateToInput.trim();
                          
                          if (!value) {
                            handleChange('auth_date_to', null);
                            return;
                          }
                          
                          // Parse the input
                          let parsed = parseDateFromInput(value);
                          
                          // If only year (YYYY), fill with 12-31
                          if (/^\d{4}$/.test(value)) {
                            parsed = `${value}-12-31`;
                          }
                          // If YYYY-MM, fill with last day of month
                          else if (/^\d{4}-\d{2}$/.test(value)) {
                            const [year, month] = value.split('-');
                            const lastDay = new Date(parseInt(year), parseInt(month), 0).getDate();
                            parsed = `${value}-${String(lastDay).padStart(2, '0')}`;
                          }
                          
                          if (parsed) {
                            const displayValue = formatDateForDisplay(parsed);
                            setAuthDateToInput(displayValue);
                            handleChange('auth_date_to', parsed);
                          }
                          
                          // Close the filter on Enter
                          if (authDateDetailsRef.current) {
                            authDateDetailsRef.current.open = false;
                          }
                        }
                      }}
                      placeholder="DD-MM-YYYY"
                      className="w-full px-3 py-2 pr-10 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                    <input
                      ref={authDateToDateInputRef}
                      type="date"
                      value={filters.auth_date_to || ''}
                      onChange={(e) => {
                        const value = e.target.value || null;
                        if (value) {
                          const displayValue = formatDateForDisplay(value);
                          setAuthDateToInput(displayValue);
                        } else {
                          setAuthDateToInput('');
                        }
                        handleChange('auth_date_to', value);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Escape' && authDateDetailsRef.current) {
                          e.preventDefault();
                          authDateDetailsRef.current.open = false;
                        } else if (e.key === 'Enter') {
                          e.preventDefault();
                          // Close the filter on Enter
                          if (authDateDetailsRef.current) {
                            authDateDetailsRef.current.open = false;
                          }
                        }
                      }}
                      className="absolute right-0 top-0 h-full w-10 opacity-0 pointer-events-none"
                      title="Use calendar picker"
                    />
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        if (authDateToDateInputRef.current) {
                          authDateToDateInputRef.current.showPicker?.();
                        }
                      }}
                      className="absolute right-0 top-0 h-full px-3 flex items-center justify-center text-gray-400 hover:text-gray-600 z-10"
                      title="Open calendar"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
              
              {(filters.auth_date_from || filters.auth_date_to) && (
                <button
                  onClick={() => {
                    setAuthDateFromInput('');
                    setAuthDateToInput('');
                    handleChange('auth_date_from', null);
                    handleChange('auth_date_to', null);
                  }}
                  className="mt-3 text-xs text-primary hover:underline"
                >
                  Clear dates
                </button>
              )}
            </div>
          </details>
        </div>

        {/* Home Member State - Multi-select (Collapsible) */}
        <div className="md:col-span-2">
          <details 
            ref={homeMemberStateDetailsRef}
            className="border border-gray-300 rounded-md"
            onToggle={(e) => {
              if (e.target.open && homeMemberStateSearchRef.current) {
                // Small delay to ensure input is rendered
                setTimeout(() => {
                  homeMemberStateSearchRef.current?.focus();
                }, 10);
              }
            }}
            onKeyDown={(e) => {
              if (e.key === 'Escape' && homeMemberStateDetailsRef.current?.open) {
                e.preventDefault();
                homeMemberStateDetailsRef.current.open = false;
              }
            }}
          >
            <summary className="px-4 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 font-medium text-gray-700 list-none">
              <div className="flex items-center justify-between">
                <span>Home Member State</span>
                <span className="text-sm font-normal text-gray-500">
                  {(filters.home_member_states || []).length > 0 
                    ? `${(filters.home_member_states || []).length} selected`
                    : 'Click to select'}
                </span>
              </div>
            </summary>
            <div className="p-3 bg-white border-t border-gray-200">
              {/* Search input */}
              <input
                ref={homeMemberStateSearchRef}
                type="text"
                value={homeMemberStateSearch}
                onChange={(e) => setHomeMemberStateSearch(e.target.value)}
                placeholder="Search countries, authorities..."
                className="w-full mb-3 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
              
              <div className="max-h-64 overflow-y-auto">
                {filterOptions.home_member_states === undefined ? (
                  <div className="text-sm text-gray-500">Loading...</div>
                ) : !Array.isArray(filterOptions.home_member_states) || filterOptions.home_member_states.length === 0 ? (
                  <div className="text-sm text-gray-500">No countries available</div>
                ) : (() => {
                  // Filter countries/authorities based on search term
                  const searchTerm = homeMemberStateSearch.toLowerCase();
                  const filteredCountries = filterOptions.home_member_states
                    .map(country => {
                      const countryName = COUNTRY_NAMES[country.country_code] || country.country_code;
                      const filteredAuthorities = country.authorities.filter(authority => {
                        const authName = typeof authority === 'string' ? authority : authority.name;
                        const authAbbr = typeof authority === 'object' && authority.abbreviation 
                          ? authority.abbreviation 
                          : (authName.match(/\(([^)]+)\)/) ? authName.match(/\(([^)]+)\)/)[1] : null);
                        
                        if (!searchTerm) return true;
                        
                        return (
                          countryName.toLowerCase().includes(searchTerm) ||
                          country.country_code.toLowerCase().includes(searchTerm) ||
                          authName.toLowerCase().includes(searchTerm) ||
                          (authAbbr && authAbbr.toLowerCase().includes(searchTerm))
                        );
                      });
                      
                      return filteredAuthorities.length > 0 
                        ? { ...country, authorities: filteredAuthorities }
                        : null;
                    })
                    .filter(Boolean);
                  
                  if (filteredCountries.length === 0) {
                    return <div className="text-sm text-gray-500">No results found</div>;
                  }
                  
                  return (
                    <>
                      <div className="grid grid-cols-1 gap-2">
                        {filteredCountries.map(country => {
                          const countryName = COUNTRY_NAMES[country.country_code] || country.country_code;
                          return country.authorities.map((authority, idx) => {
                            const authName = typeof authority === 'string' ? authority : authority.name;
                            const authAbbr = typeof authority === 'object' && authority.abbreviation 
                              ? authority.abbreviation 
                              : (authName.match(/\(([^)]+)\)/) ? authName.match(/\(([^)]+)\)/)[1] : null);
                            const displayName = authAbbr 
                              ? `${authName.replace(/\s*\([^)]+\)\s*$/, '')} (${authAbbr})`
                              : authName;
                            
                            return (
                              <label
                                key={`${country.country_code}-${idx}`}
                                className="flex items-start gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
                              >
                                <input
                                  type="checkbox"
                                  checked={(filters.home_member_states || []).includes(country.country_code)}
                                  onChange={() => handleHomeMemberStateToggle(country.country_code)}
                                  className="mt-1 rounded"
                                />
                                <span className="text-sm flex-1">
                                  {getCountryFlag(country.country_code)} {countryName} - {displayName}
                                  <span className="ml-2 text-gray-500">
                                    ({filterCounts.country_counts[country.country_code] || 0})
                                  </span>
                                </span>
                              </label>
                            );
                          });
                        })}
                      </div>
                    </>
                  );
                })()}
              </div>
              {(filters.home_member_states || []).length > 0 && (
                <button
                  onClick={() => handleChange('home_member_states', [])}
                  className="mt-2 text-xs text-primary hover:underline"
                >
                  Clear selection
                </button>
              )}
            </div>
          </details>
        </div>

        {/* Crypto-asset Services - Multi-select (Collapsible) */}
        <div className="md:col-span-2">
          <details 
            ref={cryptoServicesDetailsRef}
            className="border border-gray-300 rounded-md"
            onToggle={(e) => {
              if (e.target.open && cryptoServicesSearchRef.current) {
                // Small delay to ensure input is rendered
                setTimeout(() => {
                  cryptoServicesSearchRef.current?.focus();
                }, 10);
              }
            }}
            onKeyDown={(e) => {
              if (e.key === 'Escape' && cryptoServicesDetailsRef.current?.open) {
                e.preventDefault();
                cryptoServicesDetailsRef.current.open = false;
              }
            }}
          >
            <summary className="px-4 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 font-medium text-gray-700 list-none">
              <div className="flex items-center justify-between">
                <span>Crypto-asset services</span>
                <span className="text-sm font-normal text-gray-500">
                  {(filters.service_codes || []).length > 0 
                    ? `${(filters.service_codes || []).length} selected`
                    : 'Click to select'}
                </span>
              </div>
            </summary>
            <div className="p-3 bg-white border-t border-gray-200">
              {/* Search input */}
              <input
                ref={cryptoServicesSearchRef}
                type="text"
                value={cryptoServicesSearch}
                onChange={(e) => setCryptoServicesSearch(e.target.value)}
                placeholder="Search services..."
                className="w-full mb-3 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
              
              <div className="max-h-96 overflow-y-auto">
                {filterOptions.service_codes === undefined ? (
                  <div className="text-sm text-gray-500">Loading service codes...</div>
                ) : !Array.isArray(filterOptions.service_codes) || filterOptions.service_codes.length === 0 ? (
                  <div className="text-sm text-gray-500">
                    No service codes available
                    {process.env.NODE_ENV === 'development' && (
                      <div className="text-xs mt-1 text-gray-400">
                        Debug: {JSON.stringify(filterOptions.service_codes)}
                      </div>
                    )}
                  </div>
                ) : (() => {
                  // Filter services based on search term
                  const searchTerm = cryptoServicesSearch.toLowerCase();
                  const filteredServices = !searchTerm
                    ? filterOptions.service_codes
                    : filterOptions.service_codes.filter(service =>
                        service.description.toLowerCase().includes(searchTerm)
                      );
                  
                  if (filteredServices.length === 0) {
                    return <div className="text-sm text-gray-500">No results found</div>;
                  }
                  
                  return (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {filteredServices
                          .sort((a, b) => getServiceCodeOrder(a.code) - getServiceCodeOrder(b.code))
                          .map(service => {
                            const capitalizedDescription = getServiceDescriptionCapitalized(service.code);
                            return (
                              <label
                                key={service.code}
                                className="flex items-start gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
                              >
                                <input
                                  type="checkbox"
                                  checked={(filters.service_codes || []).includes(service.code)}
                                  onChange={() => handleServiceCodeToggle(service.code)}
                                  className="mt-1 rounded"
                                />
                                <span className="text-sm flex-1">
                                  {capitalizedDescription}
                                  <span className="ml-2 text-gray-500">
                                    ({filterCounts.service_counts[service.code] || 0})
                                  </span>
                                </span>
                              </label>
                            );
                          })}
                      </div>
                      {(filters.service_codes || []).length > 0 && (
                        <button
                          onClick={() => handleChange('service_codes', [])}
                          className="mt-2 text-xs text-primary hover:underline"
                        >
                          Clear selection
                        </button>
                      )}
                    </>
                  );
                })()}
              </div>
            </div>
          </details>
        </div>
      </div>
    </div>
  );
}


