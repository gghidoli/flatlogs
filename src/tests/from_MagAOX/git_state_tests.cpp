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

const std::string gsName{"gsName"};  // Dummy GIT repo name
const std::string gsSha1{"gsSha1"};  // Dummy GIT SHA1 value string

/** Class to encapsulate GIT State flatbuffer data using
 ** => types/git_state.hpp
 ** => types/generated/git_state_generated.h
 **/
class GSM
{
public:
  std::string m_saveGsName;    // Input parameters, unused
  std::string m_saveGsSha1;
  bool m_saveModified;

  std::string m_gsName;        // Parameters retrieved from flatbuffer
  std::string m_gsSha1;
  bool m_modified;

  int L;                       // flatbuffer data length; unused

  // Constructor
  GSM(std::string gsName_, std::string gsSha1_, bool modified_) {
    // Save inputs
    m_saveGsName = gsName_;
    m_saveGsSha1 = gsSha1_;
    m_saveModified = modified_;
  
    // Create the flatbuffer using the input parameters and...::messageT
    auto gsm = MagAOX::logger::git_state::messageT(gsName_, gsSha1_, modified_);

    // Get flatbuffer pointer and length
    void* p = gsm.builder.GetBufferPointer();
    L = MagAOX::logger::git_state::length(gsm);

    // Retrieve the flatbuffer parameters for Catch2 comparison below
    m_gsName = std::string(MagAOX::logger::git_state::repoName(p));
    m_gsSha1 = MagAOX::logger::GetGit_state_fb(p)->sha1()->c_str();
    m_modified = MagAOX::logger::GetGit_state_fb(p)->modified();
  }
};

SCENARIO( "Create", "[a log item]")
{
    GIVEN("a git_state log code")
    {
        WHEN("[modified] value is true")
        {
            bool modif{true};
            // Create flatbuffer
            GSM gs(gsName, gsSha1, modif);
            // Compare flatbuffer parameters
            REQUIRE(gs.m_gsName == gsName);
            REQUIRE(gs.m_gsSha1 == gsSha1);
            REQUIRE(gs.m_modified == modif);
        }
        WHEN("[modified] value is false")
        {
            bool modif{false};
            GSM gs(gsName, gsSha1, modif);
            REQUIRE(gs.m_gsName == gsName);
            REQUIRE(gs.m_gsSha1 == gsSha1);
            REQUIRE(gs.m_modified == modif);
        }
    }
}
