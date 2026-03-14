/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { RegisterSelector } from '../../components/RegisterSelector';

function renderSelector(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <RegisterSelector />
    </MemoryRouter>
  );
}

describe('RegisterSelector', () => {
  it('keeps the matching register active on detail routes', () => {
    renderSelector('/casp/123');

    expect(screen.getByRole('link', { name: 'CASP' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('link', { name: 'WHITE PAPER' })).not.toHaveAttribute('aria-current');
  });
});
