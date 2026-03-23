/** @vitest-environment jsdom */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { DataTable } from '../../components/DataTable';

function DataTableHarness() {
  const [sorting, setSorting] = React.useState([]);

  return (
    <div>
      <DataTable
        data={[
          {
            id: 1,
            register_type: 'other',
            lei_name: 'Circle Internet Financial',
            home_member_state: 'FR',
            lei_cou_code: 'FR',
            white_paper_url: 'https://circle.com/usdc',
            last_update: '2025-01-01',
          },
        ]}
        count={1}
        registerType="other"
        sorting={sorting}
        onSortingChange={setSorting}
        onRowClick={vi.fn()}
      />
      <div data-testid="sorting-state">{JSON.stringify(sorting)}</div>
    </div>
  );
}

import React from 'react';

describe('DataTable controlled sorting', () => {
  it('cycles sorting state through asc, desc, and none', () => {
    render(<DataTableHarness />);

    const header = screen.getByRole('columnheader', { name: /last update/i });

    fireEvent.click(header);
    expect(screen.getByTestId('sorting-state').textContent).toBe('[{"id":"last_update","desc":false}]');

    fireEvent.click(header);
    expect(screen.getByTestId('sorting-state').textContent).toBe('[{"id":"last_update","desc":true}]');

    fireEvent.click(header);
    expect(screen.getByTestId('sorting-state').textContent).toBe('[]');
  });
});
