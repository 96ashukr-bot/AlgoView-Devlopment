import React, { Fragment, useRef, useEffect, useState } from 'react';
import { Typeahead } from 'react-bootstrap-typeahead';
import { ButtonToolbar } from 'react-bootstrap';
import axios from 'axios'
import { Btn } from '../../../../AbstractElements';
import { TypeaheadDataApi } from '../../../../api';

const TypeaheadOne = () => {

  const ref = useRef();

  const [options, setOptions] = useState([])

  useEffect(() => {
    axios.get(TypeaheadDataApi).then(res => setOptions(res.data))
  }, [])

  return (
    <Fragment>
      <Typeahead
        id="public-typeahead"
        defaultSelected={options.slice(0, 4)}
        labelKey="name"
        multiple
        options={options}
        placeholder="Choose a state..."
        ref={ref}
      />
      <ButtonToolbar className="mt-2">
        <Btn attrBtn={{
          className: "mt-2"
          , onClick: () => ref.current.clear()
        }}
        >
          {"Clear"}
        </Btn>
        <Btn attrBtn={{
          className: "mt-2 ms-2",
          onClick: () => ref.current.focus()
        }}>
          {"Focus"}
        </Btn>
        <Btn attrBtn={{
          className: "mt-2 ms-2"
          , onClick: () => {
            ref.current.focus();
            setTimeout(() => ref.current.blur(), 1000);
          }
        }}>
          {"Focus, then blur after 1 second"}
        </Btn>
      </ButtonToolbar>
    </Fragment>
  );
}

export default TypeaheadOne;