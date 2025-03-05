-- catechism-filter.lua
-- A Pandoc Lua filter to transform Markdown divs into LaTeX environments

-- Function to handle the catechism question divs
function handle_question(div)
    if div.classes:includes("catechism-question") then
      -- Extract content and create custom LaTeX environment
      local content = pandoc.utils.stringify(div.content)
      local latex = "\\begin{catechismQuestion}\n" .. content .. "\n\\end{catechismQuestion}"
      
      -- Return raw LaTeX block
      return pandoc.RawBlock("latex", latex)
    end
  end
  
  -- Function to handle the catechism answer divs
  function handle_answer(div)
    if div.classes:includes("catechism-answer") then
      -- Extract content and create custom LaTeX environment
      local content = pandoc.utils.stringify(div.content)
      local latex = "\\begin{catechismAnswer}\n" .. content .. "\n\\end{catechismAnswer}"
      
      -- Return raw LaTeX block
      return pandoc.RawBlock("latex", latex)
    end
  end

  function handle_references(div)
    if div.classes:includes("scripture-references") then
      -- Get the number of columns
      local columns = div.attributes.columns or "2"
      
      -- Extract content as a string but preserve links
      local content = ""
      for _, block in ipairs(div.content) do
        if block.t == "Para" or block.t == "Plain" then
          local text = pandoc.utils.stringify(block.content)
          content = content .. text .. "\n"
        end
      end
      
      -- Create custom LaTeX environment with multicols
      local latex = "\\begin{scriptureReferences}{" .. columns .. "}\n" 
                    .. content 
                    .. "\n\\end{scriptureReferences}"
      
      return pandoc.RawBlock("latex", latex)
    end
  end