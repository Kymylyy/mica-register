import { Link, useLocation } from 'react-router-dom';

/**
 * Register selector component - tab navigation for switching between registers
 * Styled similar to GitHub's tab navigation
 */

const REGISTERS = [
  {
    id: 'casp',
    path: '/casp',
    label: 'CASPs',
    description: 'Crypto-Asset Service Providers',
  },
  {
    id: 'other',
    path: '/other',
    label: 'White Papers',
    description: 'Other Crypto-Assets White Papers',
  },
  {
    id: 'art',
    path: '/art',
    label: 'ART',
    description: 'Asset-Referenced Tokens',
  },
  {
    id: 'emt',
    path: '/emt',
    label: 'EMT',
    description: 'E-Money Tokens',
  },
  {
    id: 'ncasp',
    path: '/ncasp',
    label: 'Non-Compliant',
    description: 'Non-Compliant Entities',
  },
];

export function RegisterSelector() {
  const location = useLocation();
  const currentPath = location.pathname;

  return (
    <div className="border-b border-gray-200 mb-6">
      <nav className="flex space-x-8" aria-label="Register type selection">
        {REGISTERS.map((register) => {
          const isActive = currentPath === register.path;

          return (
            <Link
              key={register.id}
              to={register.path}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${
                  isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
              aria-current={isActive ? 'page' : undefined}
              title={register.description}
            >
              {register.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

export default RegisterSelector;
