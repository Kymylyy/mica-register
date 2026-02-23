import { useMemo, useState, useEffect, useRef } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import { FlagIcon } from './FlagIcon';
import { getServiceShortName, getServiceCodeOrder } from '../utils/serviceDescriptions';
import { getRegisterColumns, getDefaultColumnVisibility, getRegisterCounterLabel } from '../config/registerColumns';
import { getPrimaryCountryCode } from '../utils/countryNames';

const columnHelper = createColumnHelper();

// Presentational component for service tags
const ServiceTag = ({ shortName }) => (
  <span
    className="px-2.5 py-[3px] text-xs font-medium bg-sky-50 text-sky-700 rounded-full border border-sky-200"
  >
    {shortName}
  </span>
);

/**
 * Create cell renderer for a specific column
 */
const createCellRenderer = (columnId) => {
  switch (columnId) {
    case 'commercial_name':
      return (info) => {
        const commercialName = info.getValue();
        if (commercialName && commercialName.trim()) {
          return <span className="font-medium">{commercialName}</span>;
        }
        const row = info.row.original;
        return <span className="font-medium">{row.lei_name || '-'}</span>;
      };

    case 'home_member_state':
      return (info) => {
        const row = info.row.original;
        const code = getPrimaryCountryCode(info.getValue(), row.lei_cou_code);
        return (
          <div className="flex items-center gap-1.5">
            {code && <FlagIcon countryCode={code} size="sm" />}
            <span>{code || '-'}</span>
          </div>
        );
      };

    case 'authorisation_notification_date':
    case 'authorisation_end_date':
    case 'decision_date':
    case 'last_update':
    case 'white_paper_notification_date':
      return (info) => {
        const date = info.getValue();
        return date ? new Date(date).toLocaleDateString() : '-';
      };

    case 'services':
      return (info) => {
        const services = info.getValue() || [];
        if (services.length === 0) return '-';
        const sortedServices = [...services].sort((a, b) =>
          getServiceCodeOrder(a.code) - getServiceCodeOrder(b.code)
        );
        return (
          <div className="flex flex-wrap gap-2">
            {sortedServices.map((service, idx) => (
              <ServiceTag
                key={idx}
                shortName={getServiceShortName(service.code)}
              />
            ))}
          </div>
        );
      };

    case 'passport_countries':
      return (info) => {
        const countries = info.getValue() || [];
        if (countries.length === 0) return '-';
        return (
          <div className="flex flex-wrap gap-1">
            {countries.map((country, idx) => (
              <span key={idx} className="flex items-center gap-1">
                <FlagIcon countryCode={country.country_code} />
                <span className="text-xs">{country.country_code}</span>
              </span>
            ))}
          </div>
        );
      };

    case 'website':
    case 'white_paper_url':
      return (info) => {
        const url = info.getValue();
        if (!url) return '-';
        const isUrl = /^(https?:\/\/|www\.|[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,})/i.test(url.trim());
        if (!isUrl) return '-';

        // Remove protocol and www for display
        let displayUrl = url.trim().replace(/^https?:\/\//i, '').replace(/^www\./i, '');
        const href = url.startsWith('http') ? url : `https://${url}`;

        return (
          <div className="max-w-[250px] min-w-0">
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline truncate block text-sm"
              title={url}
            >
              {displayUrl}
            </a>
          </div>
        );
      };

    case 'websites':
      return (info) => {
        const websites = info.getValue();
        if (!websites) return '-';
        const websiteList = websites.split('|').map(w => w.trim()).filter(w => w);
        if (websiteList.length === 0) return '-';

        return (
          <div className="flex flex-col gap-1">
            {websiteList.map((url, idx) => {
              let displayUrl = url.replace(/^https?:\/\//i, '').replace(/^www\./i, '');
              const href = url.startsWith('http') ? url : `https://${url}`;
              return (
                <a
                  key={idx}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline break-words text-xs"
                  title={url}
                >
                  {displayUrl}
                </a>
              );
            })}
          </div>
        );
      };

    case 'lei_casp':
      return (info) => {
        const row = info.row.original;
        const leiCasp = info.getValue();
        const leiNameCasp = row.lei_name_casp;
        if (!leiCasp && !leiNameCasp) return '-';

        return (
          <div className="text-sm">
            {leiNameCasp && <div className="font-medium">{leiNameCasp}</div>}
            {leiCasp && <div className="text-xs text-gray-500">{leiCasp}</div>}
          </div>
        );
      };

    case 'offer_countries':
    case 'white_paper_offer_countries':
      return (info) => {
        const countries = info.getValue();
        if (!countries) return '-';
        const countryList = countries.split('|').map(c => c.trim()).filter(c => c);
        if (countryList.length === 0) return '-';

        return (
          <div className="flex flex-wrap gap-1">
            {countryList.map((code, idx) => (
              <span key={idx} className="flex items-center gap-1">
                <FlagIcon countryCode={code} />
                <span className="text-xs">{code}</span>
              </span>
            ))}
          </div>
        );
      };

    case 'credit_institution':
    case 'exemption_48_4':
    case 'exemption_48_5':
      return (info) => {
        const value = info.getValue();
        if (value === null || value === undefined) return '-';
        return value ? 'Yes' : 'No';
      };

    case 'dti_ffg':
      return (info) => {
        const value = info.getValue();
        return value || '-';
      };

    case 'reason':
      return (info) => {
        const reason = info.getValue();
        if (!reason || reason === 'None') return '-';
        return <span className="text-xs">{reason}</span>;
      };

    case 'lei':
    case 'lei_name':
    case 'competent_authority':
    case 'address':
    case 'comments':
    case 'white_paper_comments':
    case 'dti_codes':
    case 'authorisation_other_emt':
    case 'infringement':
      return (info) => info.getValue() || '-';

    default:
      console.warn(`No specific renderer for column: ${columnId}, using default`);
      return (info) => info.getValue() || '-';
  }
};

export function DataTable({ data, onRowClick, count, registerType = 'casp' }) {
  const [sorting, setSorting] = useState([]);

  const defaultColumnVisibility = useMemo(
    () => getDefaultColumnVisibility(registerType),
    [registerType]
  );
  const [columnVisibility, setColumnVisibility] = useState(defaultColumnVisibility);
  const detailsRef = useRef(null);
  
  // Check if current visibility matches default
  const isDefaultVisibility = useMemo(() => {
    return Object.keys(defaultColumnVisibility).every(
      key => columnVisibility[key] === defaultColumnVisibility[key]
    );
  }, [columnVisibility, defaultColumnVisibility]);
  
  // Reset to default columns
  const resetToDefault = () => {
    setColumnVisibility(defaultColumnVisibility);
  };

  // Reset column visibility when register type changes
  useEffect(() => {
    setColumnVisibility(defaultColumnVisibility);
  }, [registerType, defaultColumnVisibility]);

  // Close details when clicking outside or pressing Escape
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (detailsRef.current && !detailsRef.current.contains(event.target)) {
        if (detailsRef.current.open) {
          detailsRef.current.open = false;
        }
      }
    };
    
    const handleEscape = (event) => {
      if (event.key === 'Escape' && detailsRef.current?.open) {
        detailsRef.current.open = false;
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const columns = useMemo(() => {
    const registerColumns = getRegisterColumns(registerType);

    return registerColumns.map(colDef =>
      columnHelper.accessor(colDef.id, {
        header: colDef.label,
        size: colDef.size || 150,
        cell: createCellRenderer(colDef.id),
        meta: {
          description: colDef.description
        }
      })
    );
  }, [registerType]);

  // TanStack Table intentionally exposes function-heavy APIs that trigger this lint rule.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnVisibility,
    },
    onSortingChange: setSorting,
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  return (
    <div className="relative">
      {/* Column visibility toggle - styled as filter pill */}
      <div className="mb-3 flex justify-between items-center gap-2">
        {count !== undefined && (
          <span className="text-xs uppercase text-slate-400 tracking-wider pl-1.5">
            <span className="font-semibold text-slate-600">{count}</span> {getRegisterCounterLabel(registerType)}
          </span>
        )}
        <div className="flex items-center gap-2">
          {!isDefaultVisibility && (
            <button
              onClick={resetToDefault}
              className="px-2.5 py-1 text-xs font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-1"
              title="Reset to default columns"
            >
              Default
            </button>
          )}
          <details 
            ref={detailsRef} 
            className="relative"
            onToggle={(e) => {
              if (e.target.open) {
                // Close all filter details when opening columns
                // Find all details elements that are filters (not this one)
                const allDetails = document.querySelectorAll('details');
                allDetails.forEach(detail => {
                  // Close all details except this one (columns) and those that are already closed
                  if (detail !== e.target && detail.open) {
                    // Check if it's a filter detail (has specific structure)
                    const summary = detail.querySelector('summary');
                    if (summary && !summary.textContent?.includes('Show/Hide Columns')) {
                      detail.open = false;
                    }
                  }
                });
              }
            }}
          >
          <summary className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-gray-300 bg-white text-gray-700 text-xs font-medium cursor-pointer hover:border-sky-300 hover:bg-slate-50 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 list-none">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <span>Show/Hide Columns</span>
            <svg className="w-3.5 h-3.5 text-gray-400 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </summary>
          <div className="absolute right-0 top-full mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-50 p-3">
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {table.getAllColumns().map(column => {
                if (column.id === 'select') return null;
                let columnName = column.id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                // Ensure LEI is always uppercase
                columnName = columnName.replace(/\bLei\b/gi, 'LEI');
                return (
                  <label 
                    key={column.id} 
                    className="flex items-center gap-3 cursor-pointer hover:bg-gray-50 p-2 rounded transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={column.getIsVisible()}
                      onChange={column.getToggleVisibilityHandler()}
                      className="w-4 h-4 rounded border-gray-300 text-sky-600 focus:ring-sky-500 focus:ring-2"
                    />
                    <span className="text-sm text-gray-700 font-medium">{columnName}</span>
                  </label>
                );
              })}
            </div>
          </div>
        </details>
        </div>
      </div>

      {/* Card view for mobile/tablet */}
      <div className="block md:hidden space-y-3">
        {table.getRowModel().rows.map((row, rowIndex) => {
          const entity = row.original;
          const commercialName = entity.commercial_name?.trim() || entity.lei_name || '-';
          const homeState = getPrimaryCountryCode(entity.home_member_state, entity.lei_cou_code);
          const authDate = entity.authorisation_notification_date;
          const services = entity.services || [];
          const sortedServices = [...services].sort((a, b) => 
            getServiceCodeOrder(a.code) - getServiceCodeOrder(b.code)
          );
          
          return (
            <div
              key={row.id}
              onClick={() => onRowClick && onRowClick(entity)}
              className="bg-white border border-gray-200 rounded-lg shadow-sm p-4 cursor-pointer transition-all duration-200 hover:shadow-md hover:border-gray-300 animate-fade-in-row"
              style={{
                animationDelay: `${Math.min(rowIndex * 15, 200)}ms`,
                animationFillMode: 'both'
              }}
            >
              {/* Header */}
              <div className="mb-3 pb-3 border-b border-gray-100">
                <h3 className="font-semibold text-gray-900 leading-relaxed mb-2">{commercialName}</h3>
                <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600">
                  {homeState && (
                    <div className="flex items-center gap-1.5">
                      <FlagIcon countryCode={homeState} size="sm" />
                      <span>{homeState}</span>
                    </div>
                  )}
                  {authDate && (
                    <>
                      {homeState && <span className="text-gray-300">•</span>}
                      <span>{new Date(authDate).toLocaleDateString()}</span>
                    </>
                  )}
                </div>
              </div>
              
              {/* Services */}
              {sortedServices.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Services
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {sortedServices.map((service, idx) => {
                      const shortName = getServiceShortName(service.code);
                      return (
                        <ServiceTag
                          key={idx}
                          shortName={shortName}
                        />
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Table view for desktop */}
      <div className="hidden md:block overflow-x-auto border border-gray-200 rounded-lg shadow-sm transition-all duration-300 ease-in-out">
        <table className="min-w-full divide-y divide-gray-200 table-fixed">
          <thead className="bg-slate-50/80 backdrop-blur-sm sticky top-0 z-10 shadow-sm">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header, headerIndex) => (
                  <th
                    key={header.id}
                    className={`px-4 py-3 text-left text-[11px] font-semibold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors ${
                      headerIndex === 0 ? 'sticky left-0 z-20 bg-slate-50/80 backdrop-blur-sm' : ''
                    } ${headerIndex > 0 ? 'border-l border-gray-100' : ''}`}
                    style={{
                      width: `${header.getSize()}px`
                    }}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div className="flex items-center gap-1">
                      <span className="flex-1 min-w-0">{flexRender(header.column.columnDef.header, header.getContext())}</span>
                      {header.column.getCanSort() && (
                        <span className={`flex-shrink-0 ${
                          header.column.getIsSorted() ? 'text-blue-600' : 'text-gray-400'
                        }`}>
                          {header.column.getIsSorted() === 'asc' ? (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 15l7-7 7 7" />
                            </svg>
                          ) : header.column.getIsSorted() === 'desc' ? (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                            </svg>
                          ) : (
                            <svg className="w-4 h-4 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                            </svg>
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {table.getRowModel().rows.map((row, rowIndex) => (
              <tr
                key={row.id}
                onClick={() => onRowClick && onRowClick(row.original)}
                className={`
                  cursor-pointer transition-all duration-200 ease-in-out
                  ${rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                  hover:bg-blue-50
                  animate-fade-in-row
                `}
                style={{
                  animationDelay: `${Math.min(rowIndex * 15, 200)}ms`,
                  animationFillMode: 'both'
                }}
              >
                {row.getVisibleCells().map((cell, cellIndex) => (
                  <td 
                    key={cell.id} 
                    className={`px-4 py-4 text-sm text-gray-900 leading-relaxed ${
                      cellIndex === 0 ? 'sticky left-0 z-10 bg-inherit font-medium' : 'border-l border-gray-100'
                    }`}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
