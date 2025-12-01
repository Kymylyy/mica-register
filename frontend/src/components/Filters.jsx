import { useState, useEffect, useRef } from 'react';
import api from '../utils/api';
import { FlagIcon } from './FlagIcon';
import { getServiceDescriptionCapitalized, getServiceCodeOrder, getServiceShortName, getServiceDescription } from '../utils/serviceDescriptions';

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

export function Filters({ filters, onFiltersChange, onClearFilters, isVisible = true, onToggleVisibility }) {
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
  const authDateFromTextInputRef = useRef(null);
  const authDateToTextInputRef = useRef(null);
  const [homeMemberStateSearch, setHomeMemberStateSearch] = useState('');
  const [cryptoServicesSearch, setCryptoServicesSearch] = useState('');
  const [authDateFromInput, setAuthDateFromInput] = useState('');
  const [authDateToInput, setAuthDateToInput] = useState('');

  // Auto-format date input: add dashes after 2 and 5 digits
  const handleDateInputChange = (value, setter, inputRef) => {
    // Remove all non-digits
    const digitsOnly = value.replace(/\D/g, '');
    
    // Limit to 8 digits (DDMMYYYY)
    const limited = digitsOnly.slice(0, 8);
    
    // Format: DD-MM-YYYY
    let formatted = '';
    let cursorPos = limited.length;
    
    if (limited.length > 0) {
      formatted = limited.slice(0, 2);
      if (limited.length > 2) {
        formatted += '-' + limited.slice(2, 4);
        cursorPos = formatted.length; // Position after first dash
        if (limited.length > 4) {
          formatted += '-' + limited.slice(4, 8);
          cursorPos = formatted.length; // Position after second dash
        }
      }
    }
    
    setter(formatted);
    
    // Auto-advance cursor after adding dash
    if (inputRef && inputRef.current) {
      // If we just added a dash (at position 2 or 5), move cursor forward
      if (limited.length === 2 || limited.length === 4) {
        cursorPos = formatted.length; // Position after the dash
      }
      setTimeout(() => {
        inputRef.current.setSelectionRange(cursorPos, cursorPos);
      }, 0);
    }
  };

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
    api.get('/api/filters/options')
      .then(response => {
        // Sort service codes by MiCA order
        const sortedServiceCodes = response.data.service_codes.sort((a, b) => 
          getServiceCodeOrder(a.code) - getServiceCodeOrder(b.code)
        );
        setFilterOptions({
          ...response.data,
          service_codes: sortedServiceCodes.map(s => ({
            ...s,
            description: getServiceShortName(s.code) // Use short names like in table
          }))
        });
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
    api.get(`/api/filters/counts?${params.toString()}`)
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
    api.get(`/api/filters/counts?${params.toString()}`)
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

  // Close details when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      // Check if click is outside any details element
      const clickedElement = event.target;
      const isInsideDetails = clickedElement.closest('details');
      
      if (!isInsideDetails) {
        // Close all details elements
        if (authDateDetailsRef.current?.open) {
          authDateDetailsRef.current.open = false;
        }
        if (homeMemberStateDetailsRef.current?.open) {
          homeMemberStateDetailsRef.current.open = false;
        }
        if (cryptoServicesDetailsRef.current?.open) {
          cryptoServicesDetailsRef.current.open = false;
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleChange = (key, value) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const handleServiceCodeToggle = (code) => {
    const currentCodes = filters.service_codes || [];
    const newCodes = currentCodes.includes(code)
      ? currentCodes.filter(c => c !== code)
      : [...currentCodes, code];
    handleChange('service_codes', newCodes);
    // Clear search field after selection
    setCryptoServicesSearch('');
  };

  const handleHomeMemberStateToggle = (countryCode) => {
    const currentStates = filters.home_member_states || [];
    const newStates = currentStates.includes(countryCode)
      ? currentStates.filter(c => c !== countryCode)
      : [...currentStates, countryCode];
    handleChange('home_member_states', newStates);
    // Clear search field after selection
    setHomeMemberStateSearch('');
  };

  const handleRemoveHomeMemberState = (countryCode) => {
    const currentStates = filters.home_member_states || [];
    handleChange('home_member_states', currentStates.filter(c => c !== countryCode));
  };

  const handleRemoveServiceCode = (code) => {
    const currentCodes = filters.service_codes || [];
    handleChange('service_codes', currentCodes.filter(c => c !== code));
  };

  const handleRemoveDateFilter = () => {
    setAuthDateFromInput('');
    setAuthDateToInput('');
    // Remove both date filters at once
    const newFilters = { ...filters };
    delete newFilters.auth_date_from;
    delete newFilters.auth_date_to;
    onFiltersChange(newFilters);
  };

  const handleRemoveSearch = () => {
    handleChange('search', '');
  };

  // Get active filter count for display
  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.auth_date_from || filters.auth_date_to) count++;
    if (filters.home_member_states?.length > 0) count++;
    if (filters.service_codes?.length > 0) count++;
    return count;
  };

  const activeFilterCount = getActiveFilterCount();

  return (
    <div className="bg-white rounded-lg shadow-[0_1px_2px_rgba(0,0,0,0.04)] border border-gray-200 mb-3 animate-fade-in">
      {/* Card Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white">
        <div className="flex items-center gap-3">
          <h2 className="text-xs font-bold text-gray-800 uppercase tracking-wide">Filters</h2>
          {activeFilterCount > 0 && (
            <span className="px-2.5 py-0.5 bg-blue-600 text-white text-xs font-bold rounded-full">
              {activeFilterCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleVisibility}
            className="flex items-center gap-2 px-4 py-2 rounded-full border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 hover:border-slate-300 text-sm font-semibold cursor-pointer transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2"
            aria-label={isVisible ? 'Hide filters' : 'Show filters'}
          >
            <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            <span>{isVisible ? 'Hide filters' : 'Show filters'}</span>
            <svg 
              className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isVisible ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {activeFilterCount > 0 && (
            <button
              onClick={onClearFilters}
              className="text-sm text-red-600 hover:text-red-700 hover:bg-red-50 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1 rounded px-3 py-1.5 font-medium"
              aria-label="Clear all filters"
            >
              Clear all
            </button>
          )}
        </div>
      </div>

      {isVisible && (
        <div className="p-3 space-y-3 animate-slide-down">
          {/* Search Bar */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              value={filters.search || ''}
              onChange={(e) => handleChange('search', e.target.value)}
              placeholder="Search by anything..."
              className="w-full pl-10 pr-10 py-2 text-sm border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all hover:border-gray-400"
              aria-label="Search entities"
            />
            {filters.search && (
              <button
                onClick={() => handleChange('search', '')}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors focus:outline-none"
                aria-label="Clear search"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Active Filters Chips */}
          {(filters.search || 
            (filters.home_member_states && filters.home_member_states.length > 0) ||
            (filters.service_codes && filters.service_codes.length > 0) ||
            filters.auth_date_from || filters.auth_date_to) && (
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide mr-1">Active filters:</span>
              
              {/* Search filter chip */}
              {filters.search && (
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm font-medium border border-blue-200">
                  <span>"{filters.search}"</span>
                  <button
                    onClick={handleRemoveSearch}
                    className="ml-1 text-blue-600 hover:text-blue-700 hover:bg-blue-200 rounded-full p-0.5 transition-colors"
                    aria-label="Remove search filter"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              )}

              {/* Home Member States chips */}
              {filters.home_member_states && filters.home_member_states.length > 0 && 
                filters.home_member_states.map(countryCode => {
                  const countryName = COUNTRY_NAMES[countryCode] || countryCode;
                  return (
                    <div key={countryCode} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm font-medium border border-blue-200">
                      <FlagIcon countryCode={countryCode} size="sm" />
                      <span>{countryName}</span>
                      <button
                        onClick={() => handleRemoveHomeMemberState(countryCode)}
                        className="ml-1 text-blue-600 hover:text-blue-700 hover:bg-blue-200 rounded-full p-0.5 transition-colors"
                        aria-label={`Remove ${countryName} filter`}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  );
                })
              }

              {/* Service Codes chips */}
              {filters.service_codes && filters.service_codes.length > 0 && 
                filters.service_codes.map(code => {
                  const shortName = getServiceShortName(code);
                  const fullDescription = getServiceDescription(code);
                  return (
                    <div key={code} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm font-medium border border-blue-200" title={fullDescription}>
                      <span className="max-w-xs truncate">{shortName}</span>
                      <button
                        onClick={() => handleRemoveServiceCode(code)}
                        className="ml-1 text-blue-600 hover:text-blue-700 hover:bg-blue-200 rounded-full p-0.5 transition-colors flex-shrink-0"
                        aria-label={`Remove ${shortName} filter`}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  );
                })
              }

              {/* Date filter chip */}
              {(filters.auth_date_from || filters.auth_date_to) && (
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm font-medium border border-blue-200">
                  <span>
                    {filters.auth_date_from && filters.auth_date_to
                      ? `${formatDateForDisplay(filters.auth_date_from)} - ${formatDateForDisplay(filters.auth_date_to)}`
                      : filters.auth_date_from
                      ? `From ${formatDateForDisplay(filters.auth_date_from)}`
                      : `To ${formatDateForDisplay(filters.auth_date_to)}`}
                  </span>
                  <button
                    onClick={handleRemoveDateFilter}
                    className="ml-1 text-blue-600 hover:text-blue-800 hover:bg-blue-200 rounded-full p-0.5 transition-colors"
                    aria-label="Remove date filter"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Separator */}
          <div className="border-t border-gray-200"></div>

          {/* Filter Pills Row */}
          <div className="flex flex-wrap gap-3">
            {/* Authorisation Date Filter */}
            <details 
              ref={authDateDetailsRef}
              className="relative"
              onToggle={(e) => {
                if (e.target.open) {
                  // Close other filters when opening this one
                  if (homeMemberStateDetailsRef.current?.open) {
                    homeMemberStateDetailsRef.current.open = false;
                  }
                  if (cryptoServicesDetailsRef.current?.open) {
                    cryptoServicesDetailsRef.current.open = false;
                  }
                  // Close "Show/Hide Columns" if open
                  const allDetails = document.querySelectorAll('details');
                  allDetails.forEach(detail => {
                    if (detail !== e.target && detail.open) {
                      const summary = detail.querySelector('summary');
                      if (summary && summary.textContent?.includes('Show/Hide Columns')) {
                        detail.open = false;
                      }
                    }
                  });
                  setTimeout(() => {
                    const firstDateInput = e.target.querySelector('input[type="text"][name="auth_date_from"]');
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
              <summary className={`
                flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold cursor-pointer
                transition-all duration-200 list-none
                focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
                ${(filters.auth_date_from || filters.auth_date_to)
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md hover:shadow-lg hover:from-blue-700 hover:to-blue-800'
                  : 'bg-white text-gray-700 border-2 border-gray-300 hover:border-blue-400 hover:bg-blue-50 hover:text-blue-700'
                }
              `}>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span>Authorisation / notification date</span>
                <svg 
                  className={`w-4 h-4 transition-transform ${authDateDetailsRef.current?.open ? 'rotate-180' : ''}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="absolute top-full left-0 mt-2 w-96 bg-white border-2 border-gray-200 rounded-lg shadow-xl z-50 p-4 animate-slide-down">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {/* Date From */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      From
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        name="auth_date_from"
                        ref={authDateFromTextInputRef}
                        value={authDateFromInput}
                        onChange={(e) => {
                          handleDateInputChange(e.target.value, setAuthDateFromInput, authDateFromTextInputRef);
                        }}
                        onBlur={() => {
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
                          setAuthDateFromInput(formatDateForDisplay(value) || '');
                          handleChange('auth_date_from', value);
                        }}
                        className="absolute right-0 top-0 h-full w-10 opacity-0 pointer-events-none"
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
                        ref={authDateToTextInputRef}
                        value={authDateToInput}
                        onChange={(e) => {
                          handleDateInputChange(e.target.value, setAuthDateToInput, authDateToTextInputRef);
                        }}
                        onBlur={() => {
                          const value = authDateToInput.trim();
                          if (!value) {
                            handleChange('auth_date_to', null);
                            return;
                          }
                          let parsed = parseDateFromInput(value);
                          if (/^\d{4}$/.test(value)) {
                            parsed = `${value}-12-31`;
                          } else if (/^\d{4}-\d{2}$/.test(value)) {
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
                            let parsed = parseDateFromInput(value);
                            if (/^\d{4}$/.test(value)) {
                              parsed = `${value}-12-31`;
                            } else if (/^\d{4}-\d{2}$/.test(value)) {
                              const [year, month] = value.split('-');
                              const lastDay = new Date(parseInt(year), parseInt(month), 0).getDate();
                              parsed = `${value}-${String(lastDay).padStart(2, '0')}`;
                            }
                            if (parsed) {
                              const displayValue = formatDateForDisplay(parsed);
                              setAuthDateToInput(displayValue);
                              handleChange('auth_date_to', parsed);
                            }
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
                          setAuthDateToInput(formatDateForDisplay(value) || '');
                          handleChange('auth_date_to', value);
                        }}
                        className="absolute right-0 top-0 h-full w-10 opacity-0 pointer-events-none"
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

            {/* Home Member State Filter */}
            <details 
              ref={homeMemberStateDetailsRef}
              className="relative"
              onToggle={(e) => {
                if (e.target.open) {
                  // Close other filters when opening this one
                  if (authDateDetailsRef.current?.open) {
                    authDateDetailsRef.current.open = false;
                  }
                  if (cryptoServicesDetailsRef.current?.open) {
                    cryptoServicesDetailsRef.current.open = false;
                  }
                  // Close "Show/Hide Columns" if open
                  const allDetails = document.querySelectorAll('details');
                  allDetails.forEach(detail => {
                    if (detail !== e.target && detail.open) {
                      const summary = detail.querySelector('summary');
                      if (summary && summary.textContent?.includes('Show/Hide Columns')) {
                        detail.open = false;
                      }
                    }
                  });
                  if (homeMemberStateSearchRef.current) {
                    setTimeout(() => {
                      homeMemberStateSearchRef.current?.focus();
                    }, 10);
                  }
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Escape' && homeMemberStateDetailsRef.current?.open) {
                  e.preventDefault();
                  homeMemberStateDetailsRef.current.open = false;
                }
              }}
            >
              <summary className={`
                flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold cursor-pointer
                transition-all duration-200 list-none
                focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
                ${(filters.home_member_states || []).length > 0
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md hover:shadow-lg hover:from-blue-700 hover:to-blue-800'
                  : 'bg-white text-gray-700 border-2 border-gray-300 hover:border-blue-400 hover:bg-blue-50 hover:text-blue-700'
                }
              `}>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Home Member State</span>
                {(filters.home_member_states || []).length > 0 && (
                  <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-white/20">
                    {(filters.home_member_states || []).length}
                  </span>
                )}
                <svg 
                  className={`w-4 h-4 transition-transform ${homeMemberStateDetailsRef.current?.open ? 'rotate-180' : ''}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="absolute top-full left-0 mt-2 w-96 max-h-96 bg-white border border-gray-200 rounded-lg shadow-lg z-50 overflow-hidden flex flex-col">
                <div className="p-3 border-b-2 border-gray-200">
                  <input
                    ref={homeMemberStateSearchRef}
                    type="text"
                    value={homeMemberStateSearch}
                    onChange={(e) => setHomeMemberStateSearch(e.target.value)}
                    placeholder="Search countries, authorities..."
                    className="w-full px-3 py-2 text-sm border-2 border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary hover:border-gray-400 transition-all"
                    onKeyDown={(e) => {
                      if (e.key === 'Escape' && homeMemberStateDetailsRef.current?.open) {
                        e.preventDefault();
                        homeMemberStateDetailsRef.current.open = false;
                      }
                    }}
                  />
                </div>
                <div className="overflow-y-auto p-3">
                  {filterOptions.home_member_states === undefined ? (
                    <div className="text-sm text-gray-500">Loading...</div>
                  ) : !Array.isArray(filterOptions.home_member_states) || filterOptions.home_member_states.length === 0 ? (
                    <div className="text-sm text-gray-500">No countries available</div>
                  ) : (() => {
                    const searchTerm = homeMemberStateSearch.toLowerCase();
                    
                    // Check if there are active filters (excluding home_member_states itself)
                    const hasActiveFilters = !!(
                      filters.search || 
                      filters.service_codes?.length > 0 || 
                      filters.auth_date_from || 
                      filters.auth_date_to
                    );
                    
                    const filteredCountries = filterOptions.home_member_states
                      .map(country => {
                        const countryName = COUNTRY_NAMES[country.country_code] || country.country_code;
                        const count = filterCounts.country_counts[country.country_code] !== undefined 
                          ? filterCounts.country_counts[country.country_code] 
                          : 0;
                        
                        // Hide countries with 0 results if there are active filters
                        if (hasActiveFilters && count === 0) {
                          return null;
                        }
                        
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
                      <div className="space-y-2">
                        {filteredCountries.map(country => {
                          const countryName = COUNTRY_NAMES[country.country_code] || country.country_code;
                          const count = filterCounts.country_counts[country.country_code] !== undefined 
                            ? filterCounts.country_counts[country.country_code] 
                            : 0;
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
                                <span className="text-sm flex-1 flex items-center gap-1.5">
                                  <FlagIcon countryCode={country.country_code} size="sm" />
                                  <span>{countryName} - {displayName}</span>
                                  <span className="ml-2 text-gray-500">
                                    ({count})
                                  </span>
                                </span>
                              </label>
                            );
                          });
                        })}
                      </div>
                    );
                  })()}
                </div>
                {(filters.home_member_states || []).length > 0 && (
                  <div className="p-3 border-t border-gray-200">
                    <button
                      onClick={() => handleChange('home_member_states', [])}
                      className="text-xs text-primary hover:underline"
                    >
                      Clear selection
                    </button>
                  </div>
                )}
              </div>
            </details>

            {/* Crypto-asset Services Filter */}
            <details 
              ref={cryptoServicesDetailsRef}
              className="relative"
              onToggle={(e) => {
                if (e.target.open) {
                  // Close other filters when opening this one
                  if (authDateDetailsRef.current?.open) {
                    authDateDetailsRef.current.open = false;
                  }
                  if (homeMemberStateDetailsRef.current?.open) {
                    homeMemberStateDetailsRef.current.open = false;
                  }
                  // Close "Show/Hide Columns" if open
                  const allDetails = document.querySelectorAll('details');
                  allDetails.forEach(detail => {
                    if (detail !== e.target && detail.open) {
                      const summary = detail.querySelector('summary');
                      if (summary && summary.textContent?.includes('Show/Hide Columns')) {
                        detail.open = false;
                      }
                    }
                  });
                  if (cryptoServicesSearchRef.current) {
                    setTimeout(() => {
                      cryptoServicesSearchRef.current?.focus();
                    }, 10);
                  }
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Escape' && cryptoServicesDetailsRef.current?.open) {
                  e.preventDefault();
                  cryptoServicesDetailsRef.current.open = false;
                }
              }}
            >
              <summary className={`
                flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold cursor-pointer
                transition-all duration-200 list-none
                focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
                ${(filters.service_codes || []).length > 0
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md hover:shadow-lg hover:from-blue-700 hover:to-blue-800'
                  : 'bg-white text-gray-700 border-2 border-gray-300 hover:border-blue-400 hover:bg-blue-50 hover:text-blue-700'
                }
              `}>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
                <span>Crypto-asset services</span>
                {(filters.service_codes || []).length > 0 && (
                  <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-white/20">
                    {(filters.service_codes || []).length}
                  </span>
                )}
                <svg 
                  className={`w-4 h-4 transition-transform ${cryptoServicesDetailsRef.current?.open ? 'rotate-180' : ''}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="absolute top-full left-0 mt-2 w-96 max-h-96 bg-white border-2 border-gray-200 rounded-lg shadow-xl z-50 overflow-hidden flex flex-col animate-slide-down">
                <div className="p-3 border-b-2 border-gray-200">
                  <input
                    ref={cryptoServicesSearchRef}
                    type="text"
                    value={cryptoServicesSearch}
                    onChange={(e) => setCryptoServicesSearch(e.target.value)}
                    placeholder="Search services..."
                    className="w-full px-3 py-2 text-sm border-2 border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary hover:border-gray-400 transition-all"
                    onKeyDown={(e) => {
                      if (e.key === 'Escape' && cryptoServicesDetailsRef.current?.open) {
                        e.preventDefault();
                        cryptoServicesDetailsRef.current.open = false;
                      }
                    }}
                  />
                </div>
                <div className="overflow-y-auto p-3">
                  {filterOptions.service_codes === undefined ? (
                    <div className="text-sm text-gray-500">Loading service codes...</div>
                  ) : !Array.isArray(filterOptions.service_codes) || filterOptions.service_codes.length === 0 ? (
                    <div className="text-sm text-gray-500">No service codes available</div>
                  ) : (() => {
                    const searchTerm = cryptoServicesSearch.toLowerCase();
                    
                    // Check if there are active filters (excluding service_codes itself)
                    const hasActiveFilters = !!(
                      filters.search || 
                      filters.home_member_states?.length > 0 || 
                      filters.auth_date_from || 
                      filters.auth_date_to
                    );
                    
                    let filteredServices = !searchTerm
                      ? filterOptions.service_codes
                      : filterOptions.service_codes.filter(service =>
                          service.description.toLowerCase().includes(searchTerm)
                        );
                    
                    // Hide services with 0 results if there are active filters
                    if (hasActiveFilters) {
                      filteredServices = filteredServices.filter(service => {
                        const count = filterCounts.service_counts[service.code] !== undefined 
                          ? filterCounts.service_counts[service.code] 
                          : 0;
                        return count > 0;
                      });
                    }
                    
                    if (filteredServices.length === 0) {
                      return <div className="text-sm text-gray-500">No results found</div>;
                    }
                    
                    return (
                      <div className="space-y-2">
                        {filteredServices
                          .sort((a, b) => getServiceCodeOrder(a.code) - getServiceCodeOrder(b.code))
                          .map(service => {
                            const shortName = getServiceShortName(service.code);
                            const fullDescription = getServiceDescription(service.code);
                            const count = filterCounts.service_counts[service.code] !== undefined 
                              ? filterCounts.service_counts[service.code] 
                              : 0;
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
                                <span className="text-sm flex-1" title={fullDescription}>
                                  {shortName}
                                  <span className="ml-2 text-gray-500">
                                    ({count})
                                  </span>
                                </span>
                              </label>
                            );
                          })}
                      </div>
                    );
                  })()}
                </div>
                {(filters.service_codes || []).length > 0 && (
                  <div className="p-3 border-t border-gray-200">
                    <button
                      onClick={() => handleChange('service_codes', [])}
                      className="text-xs text-primary hover:underline"
                    >
                      Clear selection
                    </button>
                  </div>
                )}
              </div>
            </details>
          </div>
        </div>
      )}
    </div>
  );
}
