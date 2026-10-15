import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ScoreCard } from '../src/components/Results/ScoreCard';

describe('Frontend Smoke Test - ScoreCard Component', () => {
  it('renders product name and traffic-light verdict correctly', () => {
    render(
      <ScoreCard
        productName="100% Whole Wheat Atta Bread"
        healthScore={88}
        verdict="SAFE FOR YOU"
        summary="A clean whole wheat bread formulation without added sugars or artificial caramel color."
      />
    );

    expect(screen.getByText('100% Whole Wheat Atta Bread')).toBeDefined();
    expect(screen.getByText('88')).toBeDefined();
    expect(screen.getByText('SAFE FOR YOU')).toBeDefined();
  });
});
