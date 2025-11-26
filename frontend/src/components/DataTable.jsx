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
    className="px-3 py-1 text-xs font-medium bg-blue-50 text-blue-700 rounded-full cursor-help border border-blue-100"
    title={fullDescription}
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
        cell: info => info.getValue() || '-',
      }),
      columnHelper.accessor('home_member_state', {
        header: 'Home Member State',
        cell: info => {
          const code = info.getValue();
          const flag = getCountryFlag(code);
          return (
            <div className="flex items-center gap-2">
              {flag && <span>{flag}</span>}
              <span>{code || '-'}</span>
            </div>
          );
        },
      }),
      columnHelper.accessor('authorisation_notification_date', {
        header: 'Authorisation / notification date',
        cell: info => {
          const date = info.getValue();
          return date ? new Date(date).toLocaleDateString() : '-';
        },
      }),
      columnHelper.accessor('services', {
        header: 'Crypto-asset services',
        cell: info => {
          const services = info.getValue() || [];
          if (services.length === 0) return '-';
          
          // Sort services by MiCA order (a-j)
          const sortedServices = [...services].sort((a, b) => {
            return getServiceCodeOrder(a.code) - getServiceCodeOrder(b.code);
          });
          
          return (
            <div className="flex flex-wrap gap-1.5">
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
          <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-900 transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1 rounded px-3 py-1.5 flex items-center gap-2 list-none">
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
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 sticky top-0 z-10">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div className="flex items-center gap-2">
                      <span>{flexRender(header.column.columnDef.header, header.getContext())}</span>
                      {header.column.getCanSort() && (
                        <span className="text-gray-400">
                          {header.column.getIsSorted() === 'asc' ? (
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                            </svg>
                          ) : header.column.getIsSorted() === 'desc' ? (
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          ) : (
                            <svg className="w-3 h-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                  cursor-pointer transition-colors
                  ${rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                  hover:bg-blue-50
                `}
              >
                {row.getVisibleCells().map(cell => (
                  <td key={cell.id} className="px-4 py-3 text-sm text-gray-900">
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


