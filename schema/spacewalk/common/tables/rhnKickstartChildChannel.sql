--
-- Copyright (c) 2008 Red Hat, Inc.
--
-- This software is licensed to you under the GNU General Public License,
-- version 2 (GPLv2). There is NO WARRANTY for this software, express or
-- implied, including the implied warranties of MERCHANTABILITY or FITNESS
-- FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
-- along with this software; if not, see
-- http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
-- 
-- Red Hat trademarks are not licensed under GPLv2. No permission is
-- granted to use or replicate Red Hat trademarks that are incorporated
-- in this software or its documentation. 
--


CREATE TABLE rhnKickstartChildChannel
(
    channel_id  NUMBER NOT NULL 
                    CONSTRAINT rhn_ks_cc_cid_fk
                        REFERENCES rhnChannel (id) 
                        ON DELETE CASCADE, 
    ksdata_id   NUMBER NOT NULL 
                    CONSTRAINT rhn_ks_cc_ksd_fk
                        REFERENCES rhnKSData (id) 
                        ON DELETE CASCADE, 
    created     DATE 
                    DEFAULT (sysdate) NOT NULL, 
    modified    DATE 
                    DEFAULT (sysdate) NOT NULL
)
ENABLE ROW MOVEMENT
;

CREATE UNIQUE INDEX rhn_ks_cc_uq
    ON rhnKickstartChildChannel (channel_id, ksdata_id)
    TABLESPACE [[4m_tbs]];

