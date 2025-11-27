import { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import { FlagIcon, getCountryFlag } from './FlagIcon';
import { getServiceDescription, getServiceShortName, getServiceCodeOrder } from '../utils/serviceDescriptions';

const columnHelper = createColumnHelper();

// Presentational component for service tags
const ServiceTag = ({ serviceCode, fullDescription, shortName }) => (
  <span
    className="px-2 py-0.5 text-xs font-medium bg-blue-50 text-blue-700 rounded-full border border-blue-100"
  >
    {shortName}
  </span>
);

export function DataTable({ data, onRowClick }) {
  const [sorting, setSorting] = useState([]);
  const [columnVisibility, setColumnVisibility] = useState({
    commercial_name: true,
    home_member_state: true,
    authorisation_notification_date: true,
    services: true,
    // Hidden by default
    lei: false,
    lei_name: false,
    address: false,
    website: false,
    competent_authority: false,
    passport_countries: false,
    comments: false,
  });

  const columns = useMemo(
    () => [
      columnHelper.accessor('commercial_name', {
        header: 'Commercial Name',
        cell: info => {
          const commercialName = info.getValue();
          if (commercialName && commercialName.trim()) {
            return <span className="font-medium">{commercialName}</span>;
          }
          // Fallback to lei_name if commercial_name is empty
          const row = info.row.original;
          return <span className="font-medium">{row.lei_name || '-'}</span>;
        },
      }),
      columnHelper.accessor('home_member_state', {
        header: 'Home Member State',
        size: 180,
        cell: info => {
          const code = info.getValue();
          const flag = getCountryFlag(code);
          return (
            <div className="flex items-center gap-1.5">
              {flag && <span>{flag}</span>}
              <span>{code || '-'}</span>
            </div>
          );
        },
      }),
      columnHelper.accessor('authorisation_notification_date', {
        header: 'Authorisation / notification date',
        size: 200,
        cell: info => {
          const date = info.getValue();
          return date ? new Date(date).toLocaleDateString() : '-';
        },
      }),
      columnHelper.accessor('services', {
        header: 'Crypto-asset services',
        size: 400,
        cell: info => {
          const services = info.getValue() || [];
          if (services.length === 0) return '-';
          
          // Sort services by MiCA order (a-j)
          const sortedServices = [...services].sort((a, b) => {
            return getServiceCodeOrder(a.code) - getServiceCodeOrder(b.code);
          });
          
          return (
            <div className="flex flex-wrap gap-1">
              {sortedServices.map((service, idx) => {
                const fullDescription = getServiceDescription(service.code);
                const shortName = getServiceShortName(service.code);
                return (
                  <ServiceTag
                    key={idx}
                    serviceCode={service.code}
                    fullDescription={fullDescription}
                    shortName={shortName}
                  />
                );
              })}
            </div>
          );
        },
      }),
      columnHelper.accessor('lei', {
        header: 'LEI',
        cell: info => info.getValue() || '-',
      }),
      columnHelper.accessor('lei_name', {
        header: 'LEI Name',
        cell: info => info.getValue() || '-',
      }),
      columnHelper.accessor('address', {
        header: 'Address',
        cell: info => info.getValue() || '-',
      }),
      columnHelper.accessor('website', {
        header: 'Website',
        cell: info => {
          const url = info.getValue();
          return url ? (
            <a href={url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
              {url}
            </a>
          ) : '-';
        },
      }),
      columnHelper.accessor('competent_authority', {
        header: 'Competent Authority',
        cell: info => info.getValue() || '-',
      }),
      columnHelper.accessor('passport_countries', {
        header: 'Passport Countries',
        cell: info => {
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
        },
      }),
      columnHelper.accessor('comments', {
        header: 'Comments',
        cell: info => {
          const comments = info.getValue();
          return comments ? (
            <span className="text-sm text-gray-600" title={comments}>
              {comments.length > 50 ? comments.substring(0, 50) + '...' : comments}
            </span>
          ) : '-';
        },
      }),
    ],
    []
  );

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
      {/* Column visibility toggle - right-aligned ghost button */}
      <div className="mb-2 flex justify-end">
        <details className="relative">
          <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-900 transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1 rounded px-3 py-1 flex items-center gap-2 list-none">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <span>Show/Hide Columns</span>
          </summary>
          <div className="absolute right-0 top-full mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-50 p-4">
            <div className="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto">
              {table.getAllColumns().map(column => {
                if (column.id === 'select') return null;
                return (
                  <label key={column.id} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
                    <input
                      type="checkbox"
                      checked={column.getIsVisible()}
                      onChange={column.getToggleVisibilityHandler()}
                      className="rounded border-gray-300 text-primary focus:ring-primary"
                    />
                    <span className="text-sm text-gray-700">{column.id.replace(/_/g, ' ')}</span>
                  </label>
                );
              })}
            </div>
          </div>
        </details>
      </div>

      {/* Table with sticky header */}
      <div className="overflow-x-auto border border-gray-200 rounded-lg shadow-sm transition-all duration-300 ease-in-out">
        <table className="min-w-full divide-y divide-gray-200 table-fixed">
          <thead className="bg-gradient-to-b from-gray-50 to-gray-100 sticky top-0 z-10 shadow-sm">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header, headerIndex) => (
                  <th
                    key={header.id}
                    className={`px-3 py-2 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors ${
                      headerIndex === 0 ? 'sticky left-0 z-20 bg-gradient-to-b from-gray-50 to-gray-100' : ''
                    }`}
                    style={{
                      width: headerIndex === 0 ? '280px' : 
                             headerIndex === 1 ? '180px' :
                             headerIndex === 2 ? '200px' :
                             headerIndex === 3 ? 'auto' : 'auto'
                    }}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div className="flex items-center gap-2">
                      <span>{flexRender(header.column.columnDef.header, header.getContext())}</span>
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
          <tbody className="bg-white divide-y divide-gray-200">
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
                    className={`px-3 py-2 text-sm text-gray-900 ${
                      cellIndex === 0 ? 'sticky left-0 z-10 bg-inherit font-medium' : ''
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


