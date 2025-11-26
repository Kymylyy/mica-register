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
            <div className="flex flex-wrap gap-1">
              {sortedServices.map((service, idx) => {
                const fullDescription = getServiceDescription(service.code);
                const shortName = getServiceShortName(service.code);
                return (
                  <span
                    key={idx}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded cursor-help"
                    title={fullDescription}
                  >
                    {shortName}
                  </span>
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
    <div className="overflow-x-auto">
      {/* Column visibility toggle */}
      <div className="mb-4 p-2 bg-gray-50 rounded">
        <details className="text-sm">
          <summary className="cursor-pointer text-gray-700 font-medium">
            Show/Hide Columns
          </summary>
          <div className="mt-2 grid grid-cols-2 md:grid-cols-3 gap-2">
            {table.getAllColumns().map(column => {
              if (column.id === 'select') return null;
              return (
                <label key={column.id} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={column.getIsVisible()}
                    onChange={column.getToggleVisibilityHandler()}
                    className="rounded"
                  />
                  <span className="text-sm">{column.id.replace(/_/g, ' ')}</span>
                </label>
              );
            })}
          </div>
        </details>
      </div>

      {/* Table */}
      <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
        <thead className="bg-gray-50">
          {table.getHeaderGroups().map(headerGroup => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map(header => (
                <th
                  key={header.id}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={header.column.getToggleSortingHandler()}
                >
                  <div className="flex items-center gap-2">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getCanSort() && (
                      <span className="text-gray-400">
                        {{
                          asc: '↑',
                          desc: '↓',
                        }[header.column.getIsSorted()] ?? '⇅'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {table.getRowModel().rows.map(row => (
            <tr
              key={row.id}
              onClick={() => onRowClick && onRowClick(row.original)}
              className="hover:bg-gray-50 cursor-pointer"
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
  );
}


