import React, { Fragment, useState, useEffect, useCallback } from 'react';
import { Breadcrumbs } from '../../../AbstractElements';
import { Container, Row } from 'reactstrap';
import axios from 'axios';
import { Currency, WebApp, Spinner, FormControl, Directional, VideoPlayer, MedicalPlayer, TextEditor, BrandPlayer } from '../../../Constant';
import FontawesomeCommon from './FontawesomeCommon';
import IconMarkUp from '../Icon-markup';
import { FontawsomeDataApi } from '../../../api';

const FontawesomeIcon = () => {
  const [data, setData] = useState([]);
  const [iTag, setiTag] = useState('');
  const [icon, setIcon] = useState('');

  const callback = useCallback((tag) => {
    setiTag({
      iTag: '<i className="fa fa-' + tag + '"></i>',
    });
    setIcon({
      icon: 'fa fa-' + tag + ' fa-2x',
    });
  }, []);

  useEffect(() => {
    axios.get(FontawsomeDataApi).then((res) => setData(res.data));
  }, []);

  return (
    <Fragment>
      <Breadcrumbs mainTitle='Fontawesome Icons' parent='Icons' title='Fontawesome Icons' />
      <Container fluid={true}>
        {data.map((icons, index) => {
          return (
            <Row key={index}>
              <FontawesomeCommon iconType={icons.icons20} title='20' parentCallback={callback} />
              <FontawesomeCommon iconType={icons.currencyicons} title={Currency} parentCallback={callback} />
              <FontawesomeCommon iconType={icons.webicons} title={WebApp} parentCallback={callback} />
              <FontawesomeCommon iconType={icons.spinner} title={Spinner} parentCallback={callback} />
              <FontawesomeCommon iconType={icons.formicons} title={FormControl} parentCallback={callback} />
              <FontawesomeCommon iconType={icons.texteditoricons} title={TextEditor} parentCallback={callback} />
              <FontawesomeCommon iconType={icons.directionalicons} title={Directional} parentCallback={callback} />
              <FontawesomeCommon iconType={icons.videoicons} title={VideoPlayer} parentCallback={callback} />
              <FontawesomeCommon iconType={icons.branddicons} title={BrandPlayer} parentCallback={callback} />
              <FontawesomeCommon iconType={icons.medicalicons} title={MedicalPlayer} parentCallback={callback} />
            </Row>
          );
        })}
      </Container>
      <IconMarkUp itag={iTag} icons={icon} />
    </Fragment>
  );
};

export default FontawesomeIcon;
