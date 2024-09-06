import React from 'react';
import { UL, LI } from '../../../AbstractElements';

const SquareGroupUi = () => {
  return (
    <UL attrUL={{ className: 'square-group' }}>
      <LI attrLI={{ className: 'square-1 warning' }}></LI>
      <LI attrLI={{ className: 'square-1 primary' }}></LI>
      <LI attrLI={{ className: 'square-2 warning1' }}></LI>
      <LI attrLI={{ className: 'square-3 danger' }}></LI>
      <LI attrLI={{ className: 'square-4 light' }}></LI>
      <LI attrLI={{ className: 'square-5 warning' }}></LI>
      <LI attrLI={{ className: 'square-6 success' }}></LI>
      <LI attrLI={{ className: 'square-7 success' }}></LI>
    </UL>
  );
};

export default SquareGroupUi;
