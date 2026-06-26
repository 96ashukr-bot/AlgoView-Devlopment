import React, { Fragment } from 'react';
import { Route, Routes } from 'react-router-dom';
import { routes } from './Routes';
import AppLayout from '../Layout/Layout';
import LegalGate from './LegalGate';
import TermsAcceptance from '../Components/Legal/TermsAcceptance';
import RouteAccess from './RouteAccess';

const LayoutRoutes = () => {

  return (
    <>
      <Routes>
        <Route path="/terms-acceptance" element={<TermsAcceptance />} />
        <Route element={<LegalGate />}>
        {routes.map(({ path, Component }, i) => (
          <Fragment key={i}>
          <Route element={<AppLayout />} key={i}>
            <Route path={path} element={<RouteAccess>{Component}</RouteAccess>} />
          </Route>
          </Fragment>
        ))}
        </Route>
      </Routes>
    </>
  );
};

export default LayoutRoutes;
