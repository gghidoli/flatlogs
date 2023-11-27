#include <assert.h>
#include "../catch.hpp"
#include "generated/binarySchemata.inc"
#include "generated/logCodes.hpp"
////////////////////////////////////////////////////////////////////////
// todo:  use all other types/<log-type>.hpp files via
//            #include "generated/logTypes.hpp"
//        - this will be a problem because some of those <log-type>.hpp
//          header files depend on MagAOX repo.
//
#include "types/git_state.hpp"
////////////////////////////////////////////////////////////////////////
#include "types/generated/git_state_generated.h"
#include "types/flatbuffer_log.hpp"

const std::string gsName{"gsName"};
const std::string gsSha1{"gsSha1"};

class GSM
{
public:
  //MagAOX::logger::git_state::messageT gsm;
  int L;
  std::string m_saveGsName;
  std::string m_saveGsSha1;
  bool m_saveModified;
  std::string m_gsName;
  std::string m_gsSha1;
  bool m_modified;

  GSM(std::string gsName_, std::string gsSha1_, bool modified_) {
    m_saveGsName = gsName_;
    m_saveGsSha1 = gsSha1_;
    m_saveModified = modified_;
  
    auto gsm = MagAOX::logger::git_state::messageT(gsName_, gsSha1_, modified_);
    void* p= gsm.builder.GetBufferPointer();
    L = MagAOX::logger::git_state::length(gsm);

    m_gsName = std::string(MagAOX::logger::git_state::repoName(p));
    m_gsSha1 = MagAOX::logger::GetGit_state_fb(p)->sha1()->c_str();
    m_modified = MagAOX::logger::GetGit_state_fb(p)->modified();
  }
};

SCENARIO( "Create", "[a log item]")
{
    GIVEN("a git_state log code")
    {
        WHEN("with modified true")
        {
            bool modif{true};
            GSM gs(gsName, gsSha1, modif);
            REQUIRE(gs.m_gsName == gsName);
            REQUIRE(gs.m_gsSha1 == gsSha1);
            REQUIRE(gs.m_modified == modif);
        }
        WHEN("with modified false")
        {
            bool modif{false};
            GSM gs(gsName, gsSha1, modif);
            REQUIRE(gs.m_gsName == gsName);
            REQUIRE(gs.m_gsSha1 == gsSha1);
            REQUIRE(gs.m_modified == modif);
        }
    }
}
